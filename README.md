# Private Colab video renderer

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/itskrishnamalhotra-stack/colab-video-engine/blob/main/Render.ipynb)

Open the link, choose an available NVIDIA GPU, and Run all. The prepared scene,
Heart narration, word captions, music and effects are embedded in the notebook.
No manual file upload, Git clone, runtime token, Drive mount or external bridge is needed.
Colab may ask you once to sign in to GitHub and enable access to private repositories.
That browser authorization only loads the notebook; its prepared payload is already embedded.

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
The character and Blender binaries download from their publishers; they are not committed here.
No connector credentials, local authentication files, model weights or reference video are included.
