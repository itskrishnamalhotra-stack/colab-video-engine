"""Saved video workflow. Start jobs and return immediately; Python owns all waiting.

  python video_engine.py new night-file story-name
  python video_engine.py audio "E:/video engine/projects/story-name"
  python video_engine.py render "E:/video engine/projects/story-name" --after AUDIO_JOB_ID
  python video_engine.py status JOB_ID

Render jobs export cues, mix audio, render, verify, export a cover and open the MP4.
Existing videos are never regenerated merely by changing the saved defaults.
"""
from __future__ import annotations
import argparse
import ctypes
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import traceback
import uuid

ROOT = Path(__file__).resolve().parent
JOBS = ROOT / 'jobs'


def now():
    return datetime.now(timezone.utc).isoformat()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + f'.{os.getpid()}.tmp')
    temp.write_text(json.dumps(value, indent=2), encoding='utf-8')
    os.replace(temp, path)


def settings():
    return read(ROOT / 'video_defaults.json')


def child_flags():
    return {'creationflags': subprocess.CREATE_NO_WINDOW} if os.name == 'nt' else {}


def environment(cfg):
    env = os.environ.copy()
    env['PATH'] = str(Path(cfg['node']).parent) + os.pathsep + cfg['ffmpeg_bin'] + os.pathsep + env.get('PATH', '')
    env.update(PYTHONIOENCODING='utf-8', CHROME=cfg['chrome'], QS=cfg['query_settings'], FPS=str(cfg['fps']))
    # Use the local Intel GPU; do not inherit old Colab/software-render overrides.
    env.pop('RENDER_GPU', None)
    env.pop('SOFTWARE_GL', None)
    return env


def save_stage(job, stage):
    job.update(stage=stage, updated_utc=now())
    write(job['status_file'], job)


def kill_tree(proc):
    if os.name == 'nt':
        subprocess.run(['taskkill', '/PID', str(proc.pid), '/T', '/F'],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **child_flags())
    else:
        proc.kill()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        pass


def run_command(command, job, cfg, stage):
    save_stage(job, stage)
    remaining = job['deadline_epoch'] - time.time()
    if remaining <= 0:
        raise TimeoutError('The background job exceeded its configured time limit.')
    with open(job['log_file'], 'a', encoding='utf-8') as log:
        log.write(f'\n[{now()}] {stage}\n{command!r}\n')
        log.flush()
        proc = subprocess.Popen(command, cwd=job['project'], env=environment(cfg),
                                stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                                **child_flags())
        job['child_pid'] = proc.pid
        write(job['status_file'], job)
        try:
            code = proc.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            kill_tree(proc)
            raise TimeoutError(f'{stage} exceeded the job time limit; its child processes were stopped.')
    job.pop('child_pid', None)
    if code:
        raise RuntimeError(f'{stage} failed with exit code {code}. See the command output in render.log.')


def wait_for_dependency(job):
    dependency = job.get('after_status_file')
    if not dependency:
        return
    save_stage(job, 'waiting_for_audio')
    while True:
        audio = read(dependency)
        if audio['state'] == 'complete':
            return
        if audio['state'] == 'failed':
            raise RuntimeError(f'Audio job failed: {audio.get("error", "unknown error")}. Report: {audio.get("error_report")}')
        if time.time() >= job['deadline_epoch']:
            raise TimeoutError('Audio dependency did not finish within the job time limit.')
        # This wait belongs to the background Python worker, not the assistant.
        time.sleep(1)


def check_voice(project, cfg):
    from narration_profile import resolve
    selected=resolve(project,cfg)
    script = read(project / 'script.json')
    timing = read(project / 'data/lines.json')
    if script.get('voice') != selected['voice'] or timing.get('voice') != selected['voice']:
        raise ValueError(f'Narration must use the selected voice {selected["voice"]}. Run the audio command after writing the script.')
    if selected['custom']:
        provenance=read(project/'data/narration-report.json')
        if provenance.get('pack_sha256')!=selected['pack_sha256'] or provenance.get('voice')!=selected['voice']:
            raise ValueError('Prepared narration does not belong to the selected custom voice pack')
        actual=float(timing.get('speed',0))
        if actual!=float(script.get('speed',0)) or not selected['speed']<=actual<=selected['maximum_speed']:
            raise ValueError('Custom narration speed differs from its recorded bounded synthesis settings')
    for name in ('narration.wav', 'words.json'):
        if not (project / 'data' / name).is_file():
            raise FileNotFoundError(f'Missing prepared audio/timing file: data/{name}')


def verify_video(video, project, cfg):
    ffprobe = Path(cfg['ffmpeg_bin']) / ('ffprobe.exe' if os.name == 'nt' else 'ffprobe')
    result = subprocess.run([str(ffprobe), '-v', 'error', '-show_entries',
        'stream=codec_type,codec_name,width,height,duration:format=duration,size', '-of', 'json', str(video)],
        capture_output=True, text=True, encoding='utf-8', timeout=30, **child_flags())
    if result.returncode:
        raise RuntimeError('MP4 validation failed: ' + result.stderr[-1500:])
    info = json.loads(result.stdout)
    streams = info.get('streams', [])
    v = next((s for s in streams if s.get('codec_type') == 'video'), None)
    a = next((s for s in streams if s.get('codec_type') == 'audio'), None)
    if not v or not a:
        raise ValueError('MP4 is missing its video or audio stream.')
    from video_format import project_dimensions
    if (v.get('width'), v.get('height')) != project_dimensions(project):
        raise ValueError(f'Unexpected video resolution: {v.get("width")} x {v.get("height")}.')
    expected = float(read(project / 'data/lines.json')['duration'])
    duration = float(info['format']['duration'])
    if expected <= 0 or abs(duration - expected) > .25:
        raise ValueError(f'Incomplete MP4: expected {expected:.2f}s, got {duration:.2f}s.')
    return info


def open_default(path):
    if os.name != 'nt':
        raise RuntimeError('Default-player launch is configured for Windows.')
    os.startfile(str(Path(path).resolve()))


def notify_report(path, message):
    try:
        open_default(path)
    except Exception:
        if os.name == 'nt':
            ctypes.windll.user32.MessageBoxW(None, message + '\n\n' + str(path), 'Video engine', 0x10)


def report_failure(job, error, cfg):
    stage = job.get('stage', 'starting')
    log_path = Path(job['log_file'])
    text = log_path.read_text(encoding='utf-8', errors='replace') if log_path.exists() else ''
    tail = '\n'.join(text.splitlines()[-45:])
    report = Path(job['status_file']).parent / 'ERROR.txt'
    report.write_text(f'VIDEO JOB FAILED\n\nStage: {stage}\nProject: {job["project"]}\n'
        f'Cause: {error}\n\nNo successful video is being reported or opened.\n'
        f'Full log: {job["log_file"]}\n\nRECENT OUTPUT\n{tail}\n', encoding='utf-8')
    job.update(state='failed', failed_stage=stage, stage='failed', error=str(error),
               error_report=str(report), finished_utc=now())
    write(job['status_file'], job)
    if job.get('notify_errors', True):
        notify_report(report, f'Video job failed during {stage}: {error}')


def publishing_metadata(project):
    script = read(project / 'script.json')
    publishing = project / 'publishing.txt'
    text = publishing.read_text(encoding='utf-8-sig').strip() if publishing.is_file() else ''
    heading, _, body = text.partition('\n')
    title = (script.get('title') or heading or project.name.replace('-', ' ').replace('_', ' ')).strip()
    description = body.strip() or script.get('description', '').strip()
    if not description:
        description = ' '.join(line['text'].strip() for line in script.get('lines', []))
    return {'title': title, 'description': description, 'video_key': project.name}


def export_final_video(source, destination, metadata):
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix('.partial.mp4')
    metadata_file = destination.with_suffix('.json')
    try:
        shutil.copy2(source, temporary)
        # Publish the metadata before making the verified MP4 visible.
        write(metadata_file, metadata)
        os.replace(temporary, destination)
    except Exception:
        if not destination.exists():
            metadata_file.unlink(missing_ok=True)
        raise
    finally:
        temporary.unlink(missing_ok=True)
    return metadata_file


def complete_render(job, cfg):
    project = Path(job['project'])
    source = Path(job['render_file'])
    save_stage(job, 'validating_mp4')
    info = verify_video(source, project, cfg)
    destination = Path(job['output_file'])
    job['metadata_file'] = str(export_final_video(source, destination, publishing_metadata(project)))
    verification = destination.with_suffix('.verification.json')
    write(verification, info)
    job['verification_file'] = str(verification)
    # The cover is ancillary: a cover failure must not hide a valid finished MP4.
    cover = destination.with_suffix('.jpg')
    duration = float(info['format']['duration'])
    ffmpeg = str(Path(cfg['ffmpeg_bin']) / ('ffmpeg.exe' if os.name == 'nt' else 'ffmpeg'))
    try:
        run_command([ffmpeg, '-v', 'error', '-y', '-ss', str(min(2.0, duration / 2)),
            '-i', str(destination), '-frames:v', '1', '-q:v', '2', str(cover)], job, cfg, 'extracting_cover')
        job['cover_file'] = str(cover)
        if (project/'thumbnail.json').is_file():
            thumbnail=destination.with_suffix('.thumbnail.jpg')
            run_command([cfg['python'],'-u',str(ROOT/'make_story_thumbnail.py'),str(project),str(destination),str(thumbnail)],job,cfg,'creating_thumbnail')
            job['thumbnail_file']=str(thumbnail)
    except Exception as error:
        job['cover_warning'] = str(error)
    publishing = project / 'publishing.txt'
    if publishing.exists():
        shutil.copy2(publishing, destination.with_suffix('.txt'))
    job.update(state='complete', stage='complete', finished_utc=now(), player_opened=False)
    if job.get('started_utc'):
        elapsed = (datetime.fromisoformat(job['finished_utc']) - datetime.fromisoformat(job['started_utc'])).total_seconds()
        job['total_job_seconds'] = round(elapsed, 2)
    backend_path=project/'render_backend.json'
    if backend_path.is_file():
        backend=read(backend_path)
        if backend.get('timing_target_seconds') and 'total_job_seconds' in job:
            job['timing_target_met'] = elapsed <= backend['timing_target_seconds']
            timing_report=destination.with_suffix('.render-time.txt')
            timing_report.write_text(('AUDIO-ONLY UPDATE; VIDEO STREAM COPIED' if job.get('audio_only') else 'REUSED VERIFIED VIDEO' if job.get('cache_hit') else 'FRESH VIDEO RENDER')+'\n\n'
                f'Total job time, including upload, capture, download and file checks: {elapsed:.2f} seconds\n'
                f'Five-minute target: {"MET" if elapsed<=300 else "NOT MET"}\n'
                f'Three-minute preference: {"MET" if elapsed<=180 else "NOT MET"}\n'
                f'Video: {destination}\nFull log: {job["log_file"]}\n',encoding='utf-8')
            job['render_time_report']=str(timing_report)
    write(job['status_file'], job)
    if job.get('open_player', True):
        try:
            open_default(destination)
            job['player_opened'] = True
        except Exception as error:
            job['player_error'] = str(error)
            warning = destination.with_suffix('.player-error.txt')
            warning.write_text(f'The video rendered successfully, but its default player could not open.\n'
                f'Video: {destination}\nReason: {error}\n', encoding='utf-8')
            if job.get('notify_errors', True):
                notify_report(warning, 'The video is ready, but Windows could not open its player.')
    write(job['status_file'], job)


def worker(status_file):
    job = read(status_file)
    cfg = settings()
    project = Path(job['project'])
    job.update(state='running', worker_pid=os.getpid(), started_utc=now(),
               deadline_epoch=time.time() + cfg['job_timeout_seconds'])
    write(status_file, job)
    try:
        if job['kind'] in ('render','recover') and (project/'render_backend.json').is_file():
            timeout = int(read(project/'render_backend.json').get('job_timeout_seconds',cfg['job_timeout_seconds']))
            if not 30 <= timeout <= 43200:
                raise ValueError('Project render timeout must be between 30 seconds and 12 hours.')
            job['deadline_epoch'] = time.time() + timeout
            write(status_file, job)
        if job['kind'] == 'audio':
            from narration_profile import resolve
            selected=resolve(project,cfg)
            script = read(project / 'script.json')
            script.update(voice=selected['voice'], speed=selected['speed'])
            write(project / 'script.json', script)
            scripts = Path(cfg['skill_root']) / 'scripts'
            if selected['custom']:
                from cloud_narration import generate
                generate(job,cfg,selected)
            else:
                run_command([cfg['python'], '-u', str(scripts / 'voice.py'), str(project)], job, cfg, 'generating_narration')
                run_command([cfg['python'], '-u', str(scripts / 'words.py'), str(project)], job, cfg, 'aligning_words')
            if read(project/'script.json').get('radio_dialogue'):
                run_command([cfg['python'],'-u',str(ROOT/'dialogue_audio.py'),str(project)],job,cfg,'applying_radio_dialogue')
            check_voice(project, cfg)
            job.update(state='complete', stage='audio_ready', finished_utc=now())
            write(status_file, job)
        elif job['kind'] == 'remux':
            check_voice(project,cfg)
            from audio_remux import remux
            remux(job,cfg,run_command)
            complete_render(job,cfg)
            from render_reuse import remember
            try:remember(job)
            except Exception as cache_error:
                job['cache_warning']=str(cache_error);write(job['status_file'],job)
        elif job['kind'] == 'recover':
            check_voice(project,cfg)
            from webgl_recovery import recover_remote
            recover_remote(job,cfg)
            complete_render(job,cfg)
            from render_reuse import remember
            try:remember(job)
            except Exception as cache_error:
                job['cache_warning']=str(cache_error);write(job['status_file'],job)
        elif job['kind'] == 'render':
            wait_for_dependency(job)
            check_voice(project, cfg)
            backend_file = project / 'render_backend.json'
            if backend_file.is_file() and read(backend_file).get('backend') == 'blender':
                from blender_pipeline import render as render_blender
                render_blender(job, cfg, run_command)
            elif backend_file.is_file() and read(backend_file).get('backend') == 'webgl':
                from webgl_pipeline import render as render_webgl
                render_webgl(job,cfg,run_command)
            else:
                capture = str(project / 'tools/capture.mjs')
                run_command([cfg['node'], capture, 'cues'], job, cfg, 'exporting_sound_cues')
                run_command([cfg['python'], '-u', str(project / 'tools/mix.py'), str(project)], job, cfg, 'mixing_soundtrack')
                run_command([cfg['node'], capture, 'video', job['render_file']], job, cfg, 'rendering_video')
            complete_render(job, cfg)
            if backend_file.is_file() and read(backend_file).get('backend')=='webgl':
                from render_reuse import remember
                try:remember(job)
                except Exception as cache_error:
                    job['cache_warning']=str(cache_error);write(job['status_file'],job)
        else:
            raise ValueError(f'Unknown job kind: {job["kind"]}')
    except BaseException as error:
        with open(job['log_file'], 'a', encoding='utf-8') as log:
            log.write('\n' + traceback.format_exc())
        report_failure(job, error, cfg)
        return 1
    return 0


def new_project(style, name):
    if not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,79}', name):
        raise ValueError('Use a short lowercase project name with letters, digits, hyphens or underscores.')
    cfg = settings()
    source = Path(cfg['skill_root']) / 'styles' / style / 'example'
    allowed = {p.name for p in (Path(cfg['skill_root']) / 'styles').iterdir() if p.is_dir()}
    if style not in allowed or not source.is_dir():
        raise ValueError('Unknown style. Available: ' + ', '.join(sorted(allowed)))
    project = Path(cfg['project_root']) / name
    if project.exists():
        raise FileExistsError(f'Project already exists: {project}')
    shutil.copytree(source, project, ignore=shutil.ignore_patterns('narration.wav', 'mix.wav', '*.mp4', '__pycache__'))
    (project / 'renders').mkdir(exist_ok=True)
    script = read(project / 'script.json')
    script.update(voice=cfg['voice'], speed=cfg['speed'])
    write(project / 'script.json', script)
    from narration_profile import install_default
    install_default(project,cfg)
    shutil.copy2(ROOT / 'capture.mjs', project / 'tools/capture.mjs')
    if (ROOT/'cloud_capture.mjs').is_file():shutil.copy2(ROOT/'cloud_capture.mjs',project/'tools/cloud_capture.mjs')
    if (ROOT/'capture_transport.mjs').is_file():shutil.copy2(ROOT/'capture_transport.mjs',project/'tools/capture_transport.mjs')
    if style in ('tall-tale','night-file','deep-dive'):
        from install_webgl_kit import install
        install(project,activate=style=='tall-tale')
    return project


def start_job(kind, project, after=None, quiet=False, video_source=None,recover_from=None):
    cfg = settings()
    project = Path(project).resolve()
    if not (project / 'script.json').is_file():
        raise FileNotFoundError(f'No script.json in {project}')
    backend_path=project/'render_backend.json'
    if kind in ('render','remux','recover') and backend_path.is_file() and read(backend_path).get('backend')=='blender':
        raise ValueError('Blender is permanently retired by the user. Use the illustrated WebGL pipeline.')
    if kind == 'render' and not (project / 'tools/capture.mjs').is_file():
        raise FileNotFoundError('Project has no tools/capture.mjs')
    for existing in JOBS.glob('*/status.json'):
        previous = read(existing)
        if previous.get('project') == str(project) and (previous.get('kind') == kind or kind in ('render','remux','recover') and previous.get('kind') in ('render','remux','recover')) and previous.get('state') in ('queued', 'running'):
            raise RuntimeError(f'A {kind} job already exists for this project: {previous["id"]}. Check its status before launching another.')
    dependency = None
    if after:
        if not re.fullmatch(r'[0-9]{8}T[0-9]{6}-[a-f0-9]{8}', after):
            raise ValueError('Invalid dependency job ID.')
        dependency = JOBS / after / 'status.json'
        prior = read(dependency)
        if prior['kind'] != 'audio' or prior['project'] != str(project):
            raise ValueError('Dependency must be an audio job for the same project.')
    identity = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S') + '-' + uuid.uuid4().hex[:8]
    folder = JOBS / identity
    folder.mkdir(parents=True)
    status_file = folder / 'status.json'
    log_file = folder / 'render.log'
    output = Path(cfg['output_root']) / f'{project.name}-{identity}.mp4'
    job = dict(id=identity, kind=kind, project=str(project), state='queued', stage='queued',
        created_utc=now(), status_file=str(status_file), log_file=str(log_file),
        render_file=str(project / 'renders' / f'{identity}.mp4'), output_file=str(output),
        open_player=bool(cfg['open_player_on_success'] and not quiet),
        notify_errors=bool(cfg['open_error_report_on_failure'] and not quiet))
    if kind=='remux':
        source=Path(video_source or read(project/'data/render-cache.json')['video_path']).resolve()
        if not source.is_file():raise FileNotFoundError('The verified source video is missing: '+str(source))
        job['source_video']=str(source)
    if kind=='recover':
        if not recover_from or not re.fullmatch(r'[0-9]{8}T[0-9]{6}-[a-f0-9]{8}',recover_from):raise ValueError('Supply the failed render job ID')
        previous=read(JOBS/recover_from/'status.json')
        if previous.get('project')!=str(project) or previous.get('kind')!='render' or previous.get('state')!='failed' or not previous.get('colab_job_id'):
            raise ValueError('Recovery requires a failed cloud render job for this project')
        job['recover_from']=recover_from
    if dependency:
        job['after_status_file'] = str(dependency)
    write(status_file, job)
    executable = cfg['pythonw'] if os.name == 'nt' else cfg['python']
    backend_file=project/'render_backend.json'
    if kind in ('remux','recover') or kind=='render' and backend_file.is_file() and read(backend_file).get('execution')=='colab' or kind=='audio' and (project/'narrator.json').is_file():
        # The speech-only environment lacks requests; keep cloud orchestration
        # in the working host interpreter, invoking speech/mixing separately.
        executable=sys.executable
    with open(log_file, 'a', encoding='utf-8') as log:
        try:
            flags = {'creationflags': subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == 'nt' else {'start_new_session': True}
            proc = subprocess.Popen([executable, str(Path(__file__).resolve()), '_worker', str(status_file)],
                cwd=ROOT, env=environment(cfg), stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                close_fds=True, **flags)
        except Exception as error:
            report_failure(job, error, cfg)
            raise
    return dict(job_id=identity, worker_pid=proc.pid, status_file=str(status_file), log_file=str(log_file),
                output_file=str(output) if kind in ('render','remux','recover') else None, state='started_in_background')


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest='command', required=True)
    new = commands.add_parser('new')
    new.add_argument('style'); new.add_argument('name')
    for kind in ('audio', 'render','remux'):
        cmd = commands.add_parser(kind)
        cmd.add_argument('project'); cmd.add_argument('--quiet', action='store_true', help='Disable GUI notifications for automated tests.')
        if kind == 'render': cmd.add_argument('--after', help='Audio job ID to wait for automatically.')
        if kind == 'remux': cmd.add_argument('--video',help='Verified source MP4; defaults to the latest cached export.')
    status = commands.add_parser('status'); status.add_argument('job_id')
    recover=commands.add_parser('recover');recover.add_argument('job_id');recover.add_argument('--quiet',action='store_true')
    internal = commands.add_parser('_worker'); internal.add_argument('status_file')
    args = parser.parse_args()
    try:
        if args.command == 'new': print(new_project(args.style, args.name))
        elif args.command in ('audio', 'render','remux'):
            print(json.dumps(start_job(args.command, args.project, getattr(args, 'after', None), args.quiet,getattr(args,'video',None)), indent=2))
        elif args.command == 'recover':
            if not re.fullmatch(r'[0-9]{8}T[0-9]{6}-[a-f0-9]{8}',args.job_id):raise ValueError('Invalid job ID.')
            previous=read(JOBS/args.job_id/'status.json')
            print(json.dumps(start_job('recover',previous['project'],quiet=args.quiet,recover_from=args.job_id),indent=2))
        elif args.command == 'status':
            if not re.fullmatch(r'[0-9]{8}T[0-9]{6}-[a-f0-9]{8}', args.job_id): raise ValueError('Invalid job ID.')
            print(json.dumps(read(JOBS / args.job_id / 'status.json'), indent=2))
        else: return worker(args.status_file)
    except Exception as error:
        print(f'ERROR: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
