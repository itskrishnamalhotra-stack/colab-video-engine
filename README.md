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

The first run downloads official Blender 5.2.3 and Blender Studio Snow v2, checks
their hashes, selects native CUDA rendering, encodes/validates the MP4, previews
it and downloads it. A failed run downloads a diagnostic report instead.
Send the video or report back to the chat. No output is automatically published.

Current project: **The Last Cookie**, 7.405 seconds, 1080x1920, 30 fps.
This is a first production-rig performance test. CUDA speed and finished motion
quality still require the live run; reference parity is not claimed.
Free GPU assignment and session limits depend on [Colab](https://research.google.com/colaboratory/faq.html).

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
