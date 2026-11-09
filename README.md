# Reusable GPU video engine

[Open reusable GPU runtime in Colab](https://colab.research.google.com/github/itskrishnamalhotra-stack/colab-video-engine/blob/main/GPU_Runtime.ipynb)

This notebook exposes a token-protected general runtime for Python, shell/terminal,
file transfer, GPU scene tests and different video projects. It is not tied to one
scene. [Setup, tools and workflow](RUNTIME.md).

The single-scene launchers below are retained as legacy examples.

# GPU video renderer — Kaggle and Colab

[Open in Kaggle](https://www.kaggle.com/kernels/welcome?src=https://github.com/itskrishnamalhotra-stack/colab-video-engine/blob/main/Render_Kaggle.ipynb) · [Kaggle notebook source](https://github.com/itskrishnamalhotra-stack/colab-video-engine/blob/main/Render_Kaggle.ipynb)

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/itskrishnamalhotra-stack/colab-video-engine/blob/main/Render.ipynb)

## Kaggle

Open the Kaggle link, sign in, choose **Settings → Accelerator → GPU T4 ×2** if
available, turn **Internet ON**, then **Run all**. The notebook embeds the same
prepared-project hash and fetches its bundle automatically from this public repo. Nothing needs uploading and no runtime token
or dataset attachment is required. Kaggle may require account verification
before offering accelerators. GPU assignment and usage limits are controlled by Kaggle.

If the import link opens an empty notebook, use the notebook editor's
**File → Import Notebook** option and paste the Kaggle notebook source URL above.
The MP4 previews inline and is linked in the output; it is also under
`/kaggle/working/video_engine/outputs`. A failed render produces a downloadable
error report. Native CUDA rendering on Kaggle still requires its first live test.

For a saved background execution, choose **Save Version → Save & Run All** on a
clean copy of this notebook. This is Kaggle's separate batch session, with saved
logs and outputs after completion. A batch run executes every cell in order, so
exclude the earlier failed launchers. For interactive work, the optional
**Persistence → Files only** setting retains working files between supported
session restarts. Neither option guarantees recovery after a platform failure.
See [Kaggle's notebook documentation](https://www.kaggle.com/docs/notebooks).

The cloud runtime opens a fully prepared, packed `.blend` scene. Set creation,
rig pose authoring and per-frame prop baking happen locally before publishing.
The GPU job downloads/verifies the scene, prefers OptiX (CUDA fallback), enables
persistent data and high-quality GPU OIDN when supported, and renders missing
complete PNGs. Native exit codes, memory counters and the full Blender log are
recorded separately; a heartbeat reports process state every 15 seconds. No OOM
diagnosis is inferred solely from a missing session.

### Retry in an existing Kaggle session

The reported Snow-page HTTP 403 is addressed by a hash-verified, unmodified
Snow v2 archive on [our attributed release mirror](https://github.com/itskrishnamalhotra-stack/colab-video-engine/releases/tag/render-assets-v1).
The runtime no longer scrapes Blender Studio's page. Add a new cell below to
load the latest launcher while retaining the installed Blender and asset caches:

```python
import json, time, urllib.request
url = "https://raw.githubusercontent.com/itskrishnamalhotra-stack/colab-video-engine/main/Render_Kaggle.ipynb?update=" + str(time.time_ns())
nb = json.loads(urllib.request.urlopen(url).read())
exec("".join(next(c["source"] for c in nb["cells"] if c["cell_type"] == "code")))
```

## Colab

Open the link, choose an available NVIDIA GPU, and Run all. The prepared scene,
Heart narration, word captions, music and effects are embedded in the notebook.
No manual file upload, Git clone, runtime token, Drive mount or external bridge is needed.
The repository is public, so no private-repository GitHub authorization is needed.

The first run downloads official Blender 5.2.3 and the prepared scene, checks
their hashes, selects native NVIDIA rendering, encodes/validates the MP4, previews
it and downloads it. A failed run downloads a diagnostic report instead.
Send the video or report back to the chat. No output is automatically published.

Current project: **The Last Cookie**, 7.405 seconds, 1080x1920, 30 fps.
Colab T4 two-frame measurement: 16.81 seconds first frame, 7.55 seconds second
frame, GPU utilization sampled at 98% and 69.51/70 W. Original CUDA baseline was
about 56.9 seconds/frame. Resolution and sample budget are retained. Full-animation
timing and finished motion quality remain unverified; reference parity is not claimed.
Free GPU assignment and session limits depend on [Colab](https://research.google.com/colaboratory/faq.html).

## EEVEE full-video option

`Render_Parallel.ipynb` now uses two persistent Blender workers with the same
EEVEE settings. Stop the old cell first, keep the runtime connected and run the
new code in that runtime. Valid completed frames are reused. Each process loads
once and renders its complete assigned contiguous range. There is no calibration,
trial-to-production restart or automatic one-worker selection. A worker exits on
completion or failure. Cleanup is restricted to each worker's own range, so another
worker's incomplete PNG cannot be deleted. Scene/settings caches remain identical.
Blender controls temporary GPU allocations, so VRAM need not remain at a fixed
level. Memory use alone does not establish a speed gain. T4 parallel speed remains
unverified. The earlier adaptive mode is still available only via --parallel-auto.

`Render_Fast.ipynb` starts a full EEVEE video with the same packed character,
animation, meshes, textures, cameras, light objects and 1080x1920/30 fps output.
It retains the soundtrack/captions and uses 64 temporal samples, full-resolution
screen-space ray-tracing buffers, ray-trace denoising and jittered soft shadows.
EEVEE is a different rendering algorithm; indirect lighting, reflections and
subsurface appearance can differ from Cycles. It does not change the acting or
remove frames. T4 speed/finished visual quality remain unverified.
Requires a real NVIDIA OpenGL/EGL context; software rendering is refused and
NVIDIA drivers are not installed/replaced. First-frame shader initialization
can add time. Stop the previous render cell and keep the same runtime connected.
The launcher checks existing NVIDIA EGL libraries, selects the vendor through a
job-local GLVND JSON file, then verifies Blender's graphics context without
rendering a frame. Only a successful NVIDIA preflight proceeds to the full video.
Missing libraries or an unavailable context stop with graphics-status.json and
graphics-preflight.log included in the error report. No driver packages are added.
Run this full-video option in that runtime by fetching its code as in the
benchmark example below, substituting `Render_Fast.ipynb`. The resulting video
is named `artist-rig-test-eevee.mp4`; its frame cache is separate from Cycles.

## GPU optimization benchmark

`Benchmark_GPU.ipynb` renders only two full-resolution opening frames, in a new
folder, without changing the ongoing render's cached images. Stop the old render
cell first and retain the same runtime. It tries OptiX (CUDA if unavailable),
persistent render data and high-quality OpenImageDenoise on GPU when supported.
The original 1080x1920, 64-sample cap, light paths, scene and animation are retained.
The report includes native Cycles statistics, GPU utilization/power and frame
timings. No full render starts automatically. The original measured CUDA baseline
was approximately 56.9 seconds/frame on a Colab T4. The optimized test measured
16.81 seconds first frame and 7.55 seconds second frame; full-animation speed is
still unverified. These optimized settings are now the normal render defaults.
Normal runs use a separate scene-specific cache with a settings record, preserving
the previous baseline frames without mixing them into this render.

To use the existing installed runtime, add a new cell after stopping the old job:

```python
import json, time, urllib.request
url = "https://raw.githubusercontent.com/itskrishnamalhotra-stack/colab-video-engine/main/Benchmark_GPU.ipynb?update=" + str(time.time_ns())
nb = json.loads(urllib.request.urlopen(url).read())
exec("".join(next(c["source"] for c in nb["cells"] if c["cell_type"] == "code")))
```

## Files

- `Render.ipynb`: self-contained launch notebook.
- `Render_Kaggle.ipynb`: self-contained Kaggle launch notebook.
- `render-bundle.zip`: matching prepared project, soundtrack and fonts.
- `manifest.json`: hashes of the bundle contents and verified Snow archive.
- `src/`: readable snapshots of scene, script and renderer.

The local canonical source remains in E:/video engine. Rebuild this repository
from a prepared project with `python engine/prepare_github_colab.py PROJECT`, then
commit and push the refreshed files. New video concepts still need new scripts
and directed animation; this launch link automates execution of the prepared project.

## Credits

Snow Rig © Blender Foundation | studio.blender.org — [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
[Official character](https://studio.blender.org/characters/snow/v2/).
Original set, staging and animation code are included. Narrator: Kokoro Heart (`af_heart`).
Blender downloads from its publisher. The unmodified Snow archive is distributed
through the attributed GitHub Release above, verified against the inspected original's SHA-256.
Large binary dependencies are not stored in Git history.
No connector credentials, local authentication files, model weights or reference video are included.
