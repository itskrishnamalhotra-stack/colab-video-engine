# Current runtime and source

Run GPU_Runtime.ipynb from the current main branch. Reopen it from GitHub to
receive code changes; reconnecting an old open tab does not refresh its source.
The launcher caches Node/Chrome/FFmpeg once and exposes a general authenticated
runtime. It embeds no project, reference footage, narrator model or video.

src/runtime mirrors the Python runtime modules. runtime-engine.zip and the
notebook embed the same hash-verified tools. src/studio mirrors the reusable
illustrated WebGL components; src/production holds selected local orchestration,
sound and timing source. These source mirrors are not a standalone installation:
the local engine builds a complete prepared project package with pinned studio
modules, assets, sound master and browser capture tools for each job.

## Permanent visual family

The user-approved camera/body-motion benchmark is the completed one-minute
The Room That Remembers (2026-11-15). Carry forward its motivated camera travel,
varied coverage, directional body acting, connected prop handling and persistent
furnished sets within this permanent cartoon family. New stories need their own
staging and sound triggers. See src/production/PRODUCTION_LESSONS.md for the
reusable authoring cautions and recent failure corrections; the selected visual
profiles are pinned into future projects. Existing active projects are untouched.

Use the existing illustrated round heads, coherent face artwork, coat/bean body,
connected curved arms and simple hands in a 3D set. Richer clothes, seams, pockets,
hat detail and accessories enhance that family. Front/profile/back art follows
body heading; do not replace it with another character system.

EntityRegistry defines named persistent assemblies: mc owns complete character
components, center_table owns its contents, main_room owns the furnished set.
Explicit hand-socket transfer preserves prop identity. Close-ups retain connected
hands and body context, or are true object-only inserts without floating hands.
Keep room geography, wardrobe and lighting consistent across cuts.

The normal CPU sound-state evaluation checks those invariants alongside exact
animation transitions. Author relevant material sounds; do not estimate contact
positions or add a repeated editorial review loop. Default narrator: the user-selected saved am_liam_clean_1 custom pack (2026-11-15).
New projects pin the pack by hash; previous projects retain their narrator. Voice
packs and model weights remain private and are not included in this repository.
Custom inference lazily prepares/reuses an isolated CUDA Kokoro environment via
runtime_voice_setup.py. Base speed is 1.0; bounded native fitting is recorded.

## Rendering

The normal capture path composes WebGL on NVIDIA and uses the browser's native
software H.264 encoder. It does not claim hardware video encoding. Worker range
is 1-8; default one follows actual measurements. More workers cannot guarantee
more throughput. Live progress shows stages, unique completed frames and workers.

Finalization retains complete captured segments, preserves encoded video packets,
pads/trims audio to the exact frame clock, then checks frame counts and black
frames. A failed finalization is an error, not a completed video. The detached
local worker retrieves, checks and saves successful exports with metadata.

The current notebook neither installs nor executes Blender or its character
assets. Historical code remains in prior commits only. Runtime tokens, account
credentials, private source projects and AI model weights are never published.
