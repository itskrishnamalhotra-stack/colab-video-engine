"""Verify the background handoff, fixed voice, export and failure reporting without showing test dialogs."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('video_engine', HERE/'video_engine.py')
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)


class BackgroundWorkflow(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='video-engine-test-')
        self.root = Path(self.temp.name)
        self.cfg = engine.settings()
        self.cfg.update(project_root=str(self.root/'projects'), output_root=str(self.root/'exports'))

    def tearDown(self):
        # The detached worker writes final status just before its process closes
        # the inherited log handle. Windows can briefly keep that file locked.
        for attempt in range(30):
            try:
                self.temp.cleanup()
                return
            except PermissionError:
                if attempt == 29:raise
                time.sleep(.1)

    def test_every_style_starts_with_saved_narrator(self):
        with patch.object(engine, 'settings', return_value=self.cfg):
            for style in ('night-file','tall-tale','deep-dive','inside-out','stick-story','paper-atlas'):
                p = engine.new_project(style, style+'-test')
                data = engine.read(p/'script.json')
                self.assertEqual((data['voice'], data['speed']), (self.cfg['voice'],self.cfg['speed']))
                if self.cfg.get('default_narrator'):
                    from narration_profile import resolve
                    selected=resolve(p,self.cfg)
                    self.assertTrue(selected['custom'])
                    self.assertEqual(selected['pack_sha256'],self.cfg['default_narrator']['pack_sha256'])
                self.assertFalse((p/'data/narration.wav').exists())
            with self.assertRaises(FileExistsError):
                engine.new_project('night-file','night-file-test')

    def test_valid_video_is_exported_and_given_to_default_player(self):
        project = Path(r'E:\video engine\projects\mona-lisa-night-file')
        status = self.root/'job/status.json'
        job = dict(project=str(project),status_file=str(status),log_file=str(self.root/'job/render.log'),
            render_file=str(project/'renders/mona-lisa-night-file.mp4'),
            output_file=str(self.root/'exports/test.mp4'),deadline_epoch=time.time()+120,
            open_player=True,notify_errors=True)
        engine.write(status,job)
        with patch.object(engine,'open_default') as player:
            engine.complete_render(job,self.cfg)
        result=engine.read(status)
        self.assertEqual(result['state'],'complete')
        self.assertTrue(result['player_opened'])
        player.assert_called_once_with(Path(job['output_file']))
        self.assertTrue(Path(result['output_file']).is_file())
        self.assertIn('verification_file',result)
        metadata = Path(result['metadata_file'])
        self.assertEqual(metadata, Path(result['output_file']).with_suffix('.json'))
        self.assertEqual(engine.read(metadata), engine.publishing_metadata(project))

    def test_metadata_keeps_description_and_credits(self):
        engine.write(self.root/'script.json', {'title': 'The Getaway Taxi'})
        (self.root/'publishing.txt').write_text(
            'The Getaway Taxi\n\nA driver follows every rule.\n\nMusic: Composer', encoding='utf-8')
        self.assertEqual(engine.publishing_metadata(self.root), {
            'title': 'The Getaway Taxi',
            'description': 'A driver follows every rule.\n\nMusic: Composer',
            'video_key': self.root.name,
        })

    def test_command_failure_produces_readable_report(self):
        status=self.root/'failure/status.json'
        job=dict(project=str(self.root),status_file=str(status),log_file=str(self.root/'failure/render.log'),
            deadline_epoch=time.time()+30,notify_errors=True)
        engine.write(status,job)
        with self.assertRaisesRegex(RuntimeError,'exit code 9') as error:
            engine.run_command([self.cfg['node'],'-e','console.error("TEST_ENCODER_FAILURE");process.exit(9)'],job,self.cfg,'rendering_video')
        with patch.object(engine,'notify_report') as show:
            engine.report_failure(job,error.exception,self.cfg)
        result=engine.read(status)
        text=Path(result['error_report']).read_text()
        self.assertEqual(result['state'],'failed')
        self.assertIn('rendering_video',text)
        self.assertIn('exit code 9',text)
        self.assertIn('TEST_ENCODER_FAILURE',text)
        show.assert_called_once()

    def test_player_failure_keeps_valid_video_and_reports_playback_issue(self):
        project=Path(r'E:\video engine\projects\mona-lisa-night-file')
        job=dict(project=str(project),status_file=str(self.root/'player/status.json'),
            log_file=str(self.root/'player/render.log'),render_file=str(project/'renders/mona-lisa-night-file.mp4'),
            output_file=str(self.root/'exports/valid.mp4'),deadline_epoch=time.time()+120,open_player=True,notify_errors=True)
        engine.write(job['status_file'],job)
        with patch.object(engine,'open_default',side_effect=OSError('TEST_NO_PLAYER')), patch.object(engine,'notify_report') as report:
            engine.complete_render(job,self.cfg)
        self.assertEqual(engine.read(job['status_file'])['state'],'complete')
        self.assertEqual(job['player_error'],'TEST_NO_PLAYER')
        self.assertTrue(Path(job['output_file']).exists())
        report.assert_called_once()

    def test_detached_handoff_dependency_success_and_failure(self):
        isolated=self.root/'engine'
        isolated.mkdir()
        shutil.copy2(HERE/'video_engine.py',isolated/'video_engine.py')
        engine.write(isolated/'video_defaults.json',self.cfg)
        project=self.root/'smoke'
        (project/'data').mkdir(parents=True)
        (project/'tools').mkdir()
        (project/'renders').mkdir()
        engine.write(project/'script.json',dict(voice='af_heart',speed=1.0,music='none',lines=[dict(text='Background render test.')]))
        sample=Path(r'E:\video engine\voice-options\17-heart.wav')
        shutil.copy2(sample,project/'data/narration.wav')
        import wave
        with wave.open(str(sample),'rb') as audio:
            duration=audio.getnframes()/audio.getframerate()
        engine.write(project/'data/lines.json',dict(duration=duration,voice='af_heart',speed=1.0,lines=[]))
        engine.write(project/'data/words.json',[])
        shutil.copy2(Path(self.cfg['skill_root'])/'styles/night-file/example/tools/mix.py',project/'tools/mix.py')
        (project/'tools/capture.mjs').write_text('''import fs from 'node:fs';import {spawnSync} from 'node:child_process';
const [mode,out]=process.argv.slice(2),s=JSON.parse(fs.readFileSync('script.json'));
if(s.failTest){console.error('INTENTIONAL_BACKGROUND_FAILURE');process.exit(7);}
const d=JSON.parse(fs.readFileSync('data/lines.json')).duration;
if(mode==='cues'){fs.writeFileSync('data/cues.json',JSON.stringify({duration:d,cues:[]}));}
else{const p=spawnSync('ffmpeg',['-v','error','-y','-f','lavfi','-i','color=c=0x182430:s=1080x1920:r=30','-i','data/mix.wav','-t',String(d),'-c:v','libx264','-preset','ultrafast','-pix_fmt','yuv420p','-c:a','aac','-shortest',out],{stdio:'inherit'});process.exit(p.status??1);}
''',encoding='utf-8')
        dependency='20261109T000000-1234abcd'
        dep_path=isolated/'jobs'/dependency/'status.json'
        dep=dict(id=dependency,kind='audio',project=str(project.resolve()),state='running')
        engine.write(dep_path,dep)
        launch=[self.cfg['python'],str(isolated/'video_engine.py'),'render',str(project),'--after',dependency,'--quiet']
        start=time.monotonic()
        submitted=json.loads(subprocess.check_output(launch,text=True))
        self.assertLess(time.monotonic()-start,5,'Launcher blocked instead of handing off.')
        status=Path(submitted['status_file'])
        deadline=time.monotonic()+100
        while engine.read(status).get('stage')!='waiting_for_audio':
            if time.monotonic()>deadline:self.fail('Detached worker failed to start.')
            time.sleep(.2)
        # The CLI launcher has exited; the independent worker is alive and waiting.
        dep['state']='complete';engine.write(dep_path,dep)
        while engine.read(status)['state'] not in ('complete','failed'):
            if time.monotonic()>deadline:self.fail('Detached job did not complete.')
            time.sleep(.3)
        result=engine.read(status)
        self.assertEqual(result['state'],'complete',result)
        self.assertTrue(Path(result['output_file']).is_file())
        self.assertFalse(result['player_opened'])
        # A real nonzero child exit must result in an error report, never success.
        script=engine.read(project/'script.json');script['failTest']=True;engine.write(project/'script.json',script)
        submitted=json.loads(subprocess.check_output([self.cfg['python'],str(isolated/'video_engine.py'),'render',str(project),'--quiet'],text=True))
        status=Path(submitted['status_file'])
        while engine.read(status)['state'] not in ('complete','failed'):
            if time.monotonic()>deadline:self.fail('Failed job did not terminate.')
            time.sleep(.2)
        result=engine.read(status)
        self.assertEqual(result['state'],'failed')
        self.assertIn('INTENTIONAL_BACKGROUND_FAILURE',Path(result['error_report']).read_text())
        self.assertFalse(Path(result['output_file']).exists())


if __name__=='__main__':
    unittest.main(verbosity=2)
