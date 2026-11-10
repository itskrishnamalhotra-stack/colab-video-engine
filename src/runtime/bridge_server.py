"""Colab Codex Bridge: authenticated localhost execution API.

Never expose
this server on 0.0.0.0; tunnel localhost only. The bearer token grants remote
shell execution with the permissions of the Colab runtime.
"""
from __future__ import annotations

import base64
import hashlib
import collections
import json
import os
import pathlib
import secrets
import shutil
import signal
import subprocess
import sys
import threading
import time
import traceback
import uuid
from datetime import datetime, timezone
from typing import Optional

import psutil
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field

BRIDGE_DIR = pathlib.Path(os.environ.get('COLAB_BRIDGE_DIR', '/content/colab_codex_bridge')).resolve()
STATE_DIR = BRIDGE_DIR / 'state'
JOB_DIR = BRIDGE_DIR / 'jobs'
PERSIST_DIR = pathlib.Path(os.environ.get('COLAB_BRIDGE_PERSIST_DIR', '')).expanduser() if os.environ.get('COLAB_BRIDGE_PERSIST_DIR') else None
TOKEN = os.environ.get('COLAB_BRIDGE_TOKEN', '')
STARTED_AT = time.time()
MAX_FILE = 4 * 1024 * 1024
MAX_LOG_BYTES = 160000
LOCK = threading.RLock()
PROCESSES = {}
JOBS = {}
EVENTS = collections.deque(maxlen=100)
TERMINALS = {}
ENGINE_ROOT = pathlib.Path(os.environ.get('VIDEO_ENGINE_ROOT','/content/video_engine')).resolve()

def job_environment():
    env={k:v for k,v in os.environ.items() if k!='COLAB_BRIDGE_TOKEN'}
    config=ENGINE_ROOT/'gpu-environment.json'
    if config.is_file():
        values=json.loads(config.read_text())
        env.update({k:v for k,v in values.items() if k in ('__EGL_VENDOR_LIBRARY_FILENAMES','__GLX_VENDOR_LIBRARY_NAME','LD_LIBRARY_PATH')})
    return env

for d in (BRIDGE_DIR, STATE_DIR, JOB_DIR):
    d.mkdir(parents=True, exist_ok=True)

if not TOKEN or len(TOKEN) < 32:
    raise RuntimeError('COLAB_BRIDGE_TOKEN must be set to a long random secret')

app = FastAPI(title='Colab Codex Bridge', docs_url=None, redoc_url=None, openapi_url=None)


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def event(event_type: str, **values):
    with LOCK:
        EVENTS.append({'at': now(), 'event': event_type, **values})


def put_json(path: pathlib.Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.' + secrets.token_hex(4) + '.tmp')
    with temporary.open('w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.flush()
    temporary.replace(path)


def secure(authorization: Optional[str] = Header(default=None)):
    supplied = (authorization or '').removeprefix('Bearer ').strip()
    if not secrets.compare_digest(supplied, TOKEN):
        raise HTTPException(status_code=401, detail='Invalid bearer token')


def gpu_details():
    command = [
        'nvidia-smi',
        '--query-gpu=index,name,driver_version,utilization.gpu,memory.used,memory.total,temperature.gpu',
        '--format=csv,noheader,nounits'
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            return {'available': False, 'error': result.stderr.strip()[:500]}
        rows = []
        for line in result.stdout.splitlines():
            cols = [x.strip() for x in line.split(',')]
            if len(cols) >= 7:
                rows.append(dict(zip(['index', 'name', 'driver', 'utilization_percent', 'memory_used_mib',
                                      'memory_total_mib', 'temperature_c'], cols[:7])))
        return {'available': bool(rows), 'devices': rows}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {'available': False, 'error': f'{type(exc).__name__}: {exc}'}


def job_with_progress(job):
    result=job.copy()
    path=JOB_DIR/job['job_id']/'output.log'
    try:
        with path.open('rb') as stream:
            stream.seek(0,2);size=stream.tell();stream.seek(max(0,size-262144))
            lines=stream.read().split(b'\n')[:-1]
        for line in reversed(lines):
            if line.startswith((b'RENDER_PROGRESS ',b'ENGINE_PROGRESS ')):
                try:progress=json.loads(line.split(b' ',1)[1])
                except (ValueError,UnicodeError):continue
                if isinstance(progress,dict):result['progress']=progress;break
    except OSError:pass
    return result


def status():
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage(str(BRIDGE_DIR))
    with LOCK:
        running = [j['job_id'] for j in JOBS.values() if j['status'] == 'running']
        recent = list(JOBS.values())[-12:]
        events = list(EVENTS)[-15:]
    return {
        'online': True,
        'timestamp_utc': now(),
        'uptime_seconds': round(time.time() - STARTED_AT),
        'hostname': os.uname().nodename if hasattr(os, 'uname') else 'unknown',
        'python': sys.version.split()[0],
        'gpu': gpu_details(),
        'cpu_percent': psutil.cpu_percent(interval=None),
        'memory': {'total_gb': round(ram.total / 2**30, 2), 'used_gb': round(ram.used / 2**30, 2), 'available_gb': round(ram.available / 2**30, 2)},
        'disk': {'free_gb': round(disk.free / 2**30, 2), 'total_gb': round(disk.total / 2**30, 2)},
        'bridge_dir': str(BRIDGE_DIR),
        'persistent_state_dir': str(PERSIST_DIR) if PERSIST_DIR else None,
        'active_job_ids': running,
        'recent_jobs': [{k: j.get(k) for k in ('job_id', 'kind', 'status', 'exit_code', 'started_at', 'finished_at', 'command','progress')}
                        for j in map(job_with_progress,recent)],
        'events': events,
    }


def persist_snapshot():
    snapshot = status()
    put_json(STATE_DIR / 'last_status.json', snapshot)
    if PERSIST_DIR:
        try:
            PERSIST_DIR.mkdir(parents=True, exist_ok=True)
            put_json(PERSIST_DIR / 'last_status.json', snapshot)
            with LOCK:
                jobs = list(JOBS.values())[-30:]
            put_json(PERSIST_DIR / 'jobs.json', jobs)
            for job in jobs:
                source = JOB_DIR / job['job_id'] / 'output.log'
                if source.exists():
                    target = PERSIST_DIR / 'logs' / f"{job['job_id']}.log"
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with source.open('rb') as reader:
                        reader.seek(max(0, source.stat().st_size - MAX_LOG_BYTES))
                        data = reader.read()
                    target.write_bytes(data)
            (PERSIST_DIR / 'heartbeat.txt').write_text(now(), encoding='utf-8')
        except Exception as exc:
            event('persistence_error', detail=f'{type(exc).__name__}: {exc}'[:300])
    return snapshot


def background_snapshots():
    while True:
        try:
            persist_snapshot()
        except Exception as exc:
            event('snapshot_error', detail=f'{type(exc).__name__}: {exc}'[:300])
        time.sleep(15)


def wait_for_exit(job_id: str, process: subprocess.Popen):
    rc = process.wait()
    with LOCK:
        j = JOBS[job_id]
        j['status'] = 'cancelled' if j.get('cancel_requested') else ('succeeded' if rc == 0 else 'failed')
        j['exit_code'] = rc
        j['finished_at'] = now()
        put_json(JOB_DIR / job_id / 'state.json', j)
        PROCESSES.pop(job_id, None)
        event('job_finished', job_id=job_id, exit_code=rc, state=j['status'])
    try:
        persist_snapshot()
    except Exception:
        pass


def launch(command: str, kind: str, cwd: str, timeout: int, python_code: Optional[str] = None):
    job_id = str(uuid.uuid4())
    workdir = pathlib.Path(cwd).expanduser().resolve()
    if not workdir.is_dir():
        raise HTTPException(status_code=400, detail=f'Working directory not found: {workdir}')
    folder = JOB_DIR / job_id
    folder.mkdir(parents=True, exist_ok=True)
    if kind == 'python':
        script = folder / 'task.py'
        script.write_text(python_code or '', encoding='utf-8')
        argv = [sys.executable, '-u', str(script)]
        command_summary = f'python {script} (code length {len(python_code or "")})'
    else:
        argv = ['/bin/bash', '-lc', command]
        command_summary = command[:700]
    job = {
        'job_id': job_id,
        'kind': kind,
        'command': command_summary,
        'cwd': str(workdir),
        'started_at': now(),
        'finished_at': None,
        'status': 'running',
        'exit_code': None,
        'timeout_seconds': timeout,
    }
    try:
        output_handle = (folder / 'output.log').open('wb')
        process = subprocess.Popen(argv, cwd=str(workdir), stdout=output_handle,
                                   stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                   start_new_session=True, bufsize=0,
                                   env=job_environment())
        output_handle.close()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f'Failed to start: {exc}')
    with LOCK:
        JOBS[job_id] = job
        PROCESSES[job_id] = process
        put_json(folder / 'state.json', job)
        event('job_started', job_id=job_id, kind=kind)
    threading.Thread(target=wait_for_exit, args=(job_id, process), daemon=True).start()
    if timeout > 0:
        def limit():
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                with LOCK:
                    if job_id in JOBS:
                        JOBS[job_id]['timeout_reached'] = True
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
        threading.Thread(target=limit, daemon=True).start()
    return job


class CommandRequest(BaseModel):
    command: str = Field(min_length=1, max_length=100000)
    cwd: str = '/content'
    timeout_seconds: int = Field(default=3600, ge=0, le=86400)


class PythonRequest(BaseModel):
    code: str = Field(min_length=1, max_length=2000000)
    cwd: str = '/content'
    timeout_seconds: int = Field(default=3600, ge=0, le=86400)


class WriteRequest(BaseModel):
    path: str
    content_base64: str
    create_parents: bool = True

class ChunkRequest(BaseModel):
    path: str
    content_base64: str
    offset: int = Field(ge=0)

class CommitRequest(BaseModel):
    temporary: str
    path: str
    sha256: str = Field(pattern='^[0-9a-f]{64}$')
    size: int = Field(ge=0)

class TerminalWrite(BaseModel):
    text: str = Field(max_length=100000)

@app.get('/engine/capabilities',dependencies=[Depends(secure)])
def engine_capabilities():
    path=ENGINE_ROOT/'runtime-capabilities.json'
    return json.loads(path.read_text()) if path.is_file() else {'ready':False,'root':str(ENGINE_ROOT)}

@app.get('/files/stat',dependencies=[Depends(secure)])
def file_stat(path: str):
    p=pathlib.Path(path).expanduser().resolve()
    if not p.is_file():raise HTTPException(status_code=404,detail='File not found')
    with p.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
    return {'path':str(p),'size_bytes':p.stat().st_size,'sha256':digest}

@app.get('/files/read_chunk',dependencies=[Depends(secure)])
def read_chunk(path: str,offset:int=Query(default=0,ge=0),length:int=Query(default=3000000,ge=1,le=3000000)):
    p=pathlib.Path(path).expanduser().resolve()
    if not p.is_file():raise HTTPException(status_code=404,detail='File not found')
    with p.open('rb') as stream:stream.seek(offset);data=stream.read(length)
    return {'content_base64':base64.b64encode(data).decode(),'next_offset':offset+len(data),'size_bytes':p.stat().st_size}

@app.post('/files/write_chunk',dependencies=[Depends(secure)])
def write_chunk(req:ChunkRequest):
    try:data=base64.b64decode(req.content_base64,validate=True)
    except Exception:raise HTTPException(status_code=400,detail='Invalid base64')
    if len(data)>3000000:raise HTTPException(status_code=413,detail='Chunk exceeds 3 MB')
    p=pathlib.Path(req.path).expanduser().resolve();p.parent.mkdir(parents=True,exist_ok=True)
    with LOCK:
        size=p.stat().st_size if p.exists() else 0
        if size!=req.offset:raise HTTPException(status_code=409,detail='Upload offset differs from current file size')
        with p.open('ab') as stream:stream.write(data)
    return {'next_offset':req.offset+len(data)}

@app.post('/files/commit',dependencies=[Depends(secure)])
def commit_file(req:CommitRequest):
    p=pathlib.Path(req.temporary).expanduser().resolve();target=pathlib.Path(req.path).expanduser().resolve()
    if not p.is_file():raise HTTPException(status_code=404,detail='Temporary upload not found')
    with p.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
    if p.stat().st_size!=req.size or digest!=req.sha256:raise HTTPException(status_code=400,detail='Upload hash/size mismatch')
    target.parent.mkdir(parents=True,exist_ok=True);p.replace(target)
    return {'path':str(target),'sha256':digest,'size_bytes':req.size}

@app.post('/terminals',dependencies=[Depends(secure)])
def start_terminal():
    if os.name!='posix':raise HTTPException(status_code=501,detail='PTY terminals require Linux')
    import pty
    master,slave=pty.openpty();env=job_environment();env.update(TERM='xterm-256color',PS1='gpu-runtime> ')
    process=subprocess.Popen(['/bin/bash','--noprofile','--norc','-i'],stdin=slave,stdout=slave,stderr=slave,start_new_session=True,env=env,cwd=str(ENGINE_ROOT if ENGINE_ROOT.is_dir() else BRIDGE_DIR))
    os.close(slave);identifier=str(uuid.uuid4());folder=BRIDGE_DIR/'terminals'/identifier;folder.mkdir(parents=True)
    entry={'process':process,'master':master,'log':folder/'output.log'}
    with LOCK:TERMINALS[identifier]=entry
    def read_output():
        with entry['log'].open('ab',buffering=0) as output:
            try:
                while data:=os.read(master,4096):output.write(data)
            except OSError:pass
        process.wait()
        try:os.close(master)
        except OSError:pass
    threading.Thread(target=read_output,daemon=True).start()
    return {'terminal_id':identifier,'pid':process.pid}

@app.get('/terminals/{identifier}/read',dependencies=[Depends(secure)])
def read_terminal(identifier:str,offset:int=Query(default=0,ge=0),limit:int=Query(default=30000,ge=1,le=MAX_LOG_BYTES)):
    with LOCK:entry=TERMINALS.get(identifier)
    if entry is None:raise HTTPException(status_code=404,detail='Unknown terminal')
    data=b''
    if entry['log'].is_file():
        with entry['log'].open('rb') as stream:stream.seek(offset);data=stream.read(limit)
    return {'text':data.decode('utf-8',errors='replace'),'next_offset':offset+len(data),'running':entry['process'].poll() is None}

@app.post('/terminals/{identifier}/write',dependencies=[Depends(secure)])
def write_terminal(identifier:str,req:TerminalWrite):
    with LOCK:entry=TERMINALS.get(identifier)
    if entry is None:raise HTTPException(status_code=404,detail='Unknown terminal')
    if entry['process'].poll() is not None:raise HTTPException(status_code=409,detail='Terminal has exited')
    try:os.write(entry['master'],req.text.encode())
    except OSError:raise HTTPException(status_code=409,detail='Terminal is closed')
    return {'ok':True}

@app.post('/terminals/{identifier}/close',dependencies=[Depends(secure)])
def close_terminal(identifier:str):
    with LOCK:entry=TERMINALS.get(identifier)
    if entry is None:raise HTTPException(status_code=404,detail='Unknown terminal')
    if entry['process'].poll() is None:
        try:os.killpg(entry['process'].pid,signal.SIGHUP)
        except ProcessLookupError:pass
    return {'ok':True}


@app.get('/health', dependencies=[Depends(secure)])
def health():
    return {'status': 'ok', 'timestamp_utc': now(), 'api_version': 3}

@app.on_event('shutdown')
def shutdown_children():
    with LOCK:
        children=list(PROCESSES.values())+[entry['process'] for entry in TERMINALS.values()]
        for job in JOBS.values():
            if job['status']=='running':job['cancel_requested']=True
    for process in children:
        if process.poll() is None:
            try:
                if os.name=='posix':os.killpg(process.pid,signal.SIGTERM)
                else:process.terminate()
            except ProcessLookupError:pass


@app.get('/status', dependencies=[Depends(secure)])
def read_status():
    s = status()
    put_json(STATE_DIR / 'last_status.json', s)
    return s


@app.post('/jobs/command', dependencies=[Depends(secure)])
def command_job(req: CommandRequest):
    return launch(req.command, 'shell', req.cwd, req.timeout_seconds)


@app.post('/jobs/python', dependencies=[Depends(secure)])
def python_job(req: PythonRequest):
    return launch('', 'python', req.cwd, req.timeout_seconds, python_code=req.code)


@app.get('/jobs', dependencies=[Depends(secure)])
def list_jobs(limit: int = Query(default=20, ge=1, le=100)):
    with LOCK:
        return [job_with_progress(j) for j in list(JOBS.values())[-limit:]]


@app.get('/jobs/{job_id}', dependencies=[Depends(secure)])
def get_job(job_id: str):
    with LOCK:
        if job_id not in JOBS:
            raise HTTPException(status_code=404, detail='Unknown job ID')
        return job_with_progress(JOBS[job_id])


@app.get('/jobs/{job_id}/output', dependencies=[Depends(secure)])
def job_output(job_id: str, offset: int = Query(default=0, ge=0), limit: int = Query(default=30000, ge=1, le=MAX_LOG_BYTES)):
    with LOCK:
        if job_id not in JOBS:
            raise HTTPException(status_code=404, detail='Unknown job ID')
        job = job_with_progress(JOBS[job_id])
    p = JOB_DIR / job_id / 'output.log'
    size = p.stat().st_size if p.exists() else 0
    with p.open('rb') as f:
        f.seek(min(offset, size))
        chunk = f.read(limit)
    return {'job': job, 'text': chunk.decode('utf-8', errors='replace'),
            'offset': offset, 'next_offset': min(offset, size) + len(chunk),
            'total_bytes': size, 'has_more': min(offset, size) + len(chunk) < size}


@app.post('/jobs/{job_id}/cancel', dependencies=[Depends(secure)])
def cancel_job(job_id: str):
    with LOCK:
        process = PROCESSES.get(job_id)
        if job_id not in JOBS:
            raise HTTPException(status_code=404, detail='Unknown job ID')
        if not process or process.poll() is not None:
            return {'ok': False, 'detail': 'Job already finished'}
        JOBS[job_id]['cancel_requested'] = True
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    return {'ok': True, 'job_id': job_id}


@app.get('/files/list', dependencies=[Depends(secure)])
def files_list(path: str = '/content', limit: int = Query(default=100, ge=1, le=500)):
    p = pathlib.Path(path).expanduser().resolve()
    if not p.is_dir():
        raise HTTPException(status_code=400, detail='Not a directory')
    try:
        items = sorted(p.iterdir(), key=lambda f: (not f.is_dir(), f.name.lower()))[:limit]
        return {'path': str(p), 'items': [{'name': x.name, 'is_dir': x.is_dir(), 'size_bytes': x.stat().st_size if x.is_file() else None}
                                           for x in items]}
    except OSError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get('/files/read', dependencies=[Depends(secure)])
def files_read(path: str):
    p = pathlib.Path(path).expanduser().resolve()
    if not p.is_file():
        raise HTTPException(status_code=404, detail='File not found')
    size = p.stat().st_size
    if size > MAX_FILE:
        raise HTTPException(status_code=413, detail='File too large for direct transfer; use shell commands or chunked transfer')
    return {'path': str(p), 'content_base64': base64.b64encode(p.read_bytes()).decode('ascii'), 'size_bytes': size}


@app.post('/files/write', dependencies=[Depends(secure)])
def files_write(req: WriteRequest):
    try:
        data = base64.b64decode(req.content_base64, validate=True)
    except Exception:
        raise HTTPException(status_code=400, detail='Invalid base64 data')
    if len(data) > MAX_FILE:
        raise HTTPException(status_code=413, detail='File too large for direct transfer')
    p = pathlib.Path(req.path).expanduser().resolve()
    if req.create_parents:
        p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    return {'path': str(p), 'size_bytes': len(data)}


@app.get('/recovery', dependencies=[Depends(secure)])
def recovery():
    # This endpoint is useful after transient tunnel failure while VM lives.
    with LOCK:
        recent = list(JOBS.values())[-20:]
        events = list(EVENTS)
    log_tails = {}
    for j in recent[-8:]:
        p = JOB_DIR / j['job_id'] / 'output.log'
        if p.exists():
            with p.open('rb') as f:
                f.seek(max(0, p.stat().st_size - 2000))
                log_tails[j['job_id']] = f.read().decode('utf-8', errors='replace')
    return {'status': status(), 'recent_jobs': recent, 'events': events, 'recent_output_tails': log_tails}


def restore_local_history():
    for folder in JOB_DIR.glob('*/state.json'):
        try:
            old = json.loads(folder.read_text('utf-8'))
            if old.get('status') == 'running':
                old['status'] = 'interrupted_or_unknown'
                old['finished_at'] = now()
            JOBS[old['job_id']] = old
        except Exception:
            pass
    event('bridge_started', restored_jobs=len(JOBS))


restore_local_history()
threading.Thread(target=background_snapshots, daemon=True).start()
