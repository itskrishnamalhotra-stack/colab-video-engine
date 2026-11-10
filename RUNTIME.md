# Reusable GPU runtime

Host RAM correction: four scene copies exceeded the 12.7 GB VM's system RAM in
the first live attempt, with no completed frames and one killed worker. Worker
admission now uses available host RAM: 2 GiB reserve and an estimated 3.5 GiB per
Blender scene. This VM normally admits two; larger RAM can admit four. A request
for four is an upper bound, not an instruction to exceed available RAM. Rendering
settings and animation are retained. Progress/logs now include host RAM and
per-worker RSS; sustained critical headroom ends the job cleanly with cached
completed frames retained. Failure progress is updated after all peers stop.

Open GPU_Runtime.ipynb in Google Colab, select an NVIDIA GPU and run its cell.
It prints a temporary HTTPS URL and a private token. The service supports arbitrary
Python, shell command jobs, an interactive Linux PTY, upload/download, output logs,
cancellation, and native GPU access. No particular video is embedded. Google Drive
is not mounted. Keep the token private: it grants execution and file access.

The first setup downloads verified Blender, system libraries and the attributed
Snow character. Tools/assets are cached for the life of that VM. The EGL selection
fix is included. A new/deleted VM needs setup again; rerunning in the same live VM
reuses the authenticated server and jobs and refreshes its tunnel. Provider limits
and external-control restrictions still apply; no uptime guarantee is made.

On the Windows workstation, open E:/video engine and double-click Connect_Runtime.cmd
(or run `python engine/gpu_runtime.py connect`). Enter the URL and private token.
They are saved under the user's private .colab-codex folder, never in this repo.
The phone can start the notebook; no mouse connection to it is needed afterward.

## Commands from E:/video engine

```
python engine/gpu_runtime.py status
python engine/gpu_runtime.py upload local-file.py /content/my-file.py
python engine/gpu_runtime.py python local-file.py
python engine/gpu_runtime.py shell local-commands.sh
python engine/gpu_runtime.py job JOB_ID
python engine/gpu_runtime.py cancel JOB_ID
python engine/gpu_runtime.py download /content/result.mp4 "E:/video engine/outputs/result.mp4"
python engine/gpu_runtime.py terminal-start
python engine/gpu_runtime.py terminal-write TERMINAL_ID "nvidia-smi"
python engine/gpu_runtime.py terminal-read TERMINAL_ID
python engine/gpu_runtime.py terminal-close TERMINAL_ID
```

File transfers use 3 MB chunks and verify SHA-256 before committing the destination.
The API also supports interactive terminal input/output; Windows local tests check
platform gating, while the Linux PTY still needs live validation.

## Video projects and small GPU tests

```
python engine/gpu_runtime.py project projects/PROJECT --task build
python engine/gpu_runtime.py project projects/PROJECT --task probe --first 96
python engine/gpu_runtime.py project projects/PROJECT --task render --workers 4
```

These commands upload project source/audio/assets without reference videos, caches
or private model weights. Source-based Blender projects provide build_scene.py
with --project, --frames and --prepare-only arguments, producing prepared-scene.blend
and prepared-scene.json. Rig source assets are available from the shared cache.
The GPU runtime performs preparation and rendering; the laptop does not render.
Probes select up to 32 consecutive frames at full resolution; completed images are
retrieved automatically. Full video jobs retain narration, music/effects and captions,
perform the basic MP4 check, download and open the video. The four Blender workers
load their scenes once and retain their assigned full frame ranges.

Four persistent EEVEE workers are the current default. Choose --workers 1, 2, 3
or 4 for a new job without changing source or publishing again. Existing running
jobs keep their worker count. Four workers are locally tested for orchestration;
their throughput on a T4 is not yet measured. GPU memory may fluctuate and more
workers do not guarantee a speedup.

The running notebook shows a live dashboard, refreshed every 3 seconds. It counts
unique completed frames across all workers, includes cached frames, and shows
each worker's status, current frame, completed range and PID. Overall elapsed
render time, measured frame rate and estimated remaining render time appear
after sufficient frames finish. Loading and encoding are separate stages; ETA
does not include encoding or file transfer. A static high frame number from a
later worker is never used as the total completed count. The local detached
watcher's status.json also records progress and downloaded bytes.

The project command returns a job ID immediately and starts a hidden local watcher.
Logs, status and errors are under engine/jobs/runtime-REQUEST_ID; results go to
E:/video engine/outputs. The watcher reports failures; it does not repair animation.
The normal `python engine/video_engine.py render projects/PROJECT` also uses this
runtime for Blender projects with execution set to colab.

The connection is general-purpose: subsequent projects use the same notebook and
URL while the runtime lives. Reconnect only when its URL/token changes. This repo
still contains the earlier single-scene notebooks as legacy examples.

Snow Rig © Blender Foundation | studio.blender.org — CC BY 4.0.
