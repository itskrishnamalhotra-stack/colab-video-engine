# Binary frames and hardware encoding

Shared kit 1.3.1 adds a bounded binary localhost path:

1. Three.js renders into its owned RGBA8 target.
2. The synchronized readback and Canvas captions/fades remain unchanged.
3. `OP.rawFrame` POSTs the final RGBA bytes to a random localhost capture route.
4. Node streams the body into FFmpeg with backpressure and strict frame sequence,
   content length and completion checks. No JPEG/base64 encode/decode step.
5. A live full-HD NVENC encode/metadata probe selects H.264 hardware encoding
   when available. RGBA input is accepted directly by NVENC on the tested T4;
   encoded output is checked as compatible H.264/YUV420. Production CQP is 16.
6. Frame-count, MP4/audio/duration and blank-frame guards stay enabled.

This still copies pixels out of WebGL. It is not zero-copy GPU capture.
NVENC CQP16 and x264 CRF18 are different encoding modes, not bit-identical output.
The raw source avoids an intermediate lossy JPEG stage. No resolution, frame
rate, antialiasing, shadow, character detail or action timing is reduced.

Standing/sitting/jumping character art now ignores the unused walk phase in its
cache key. `drawToon` reads phase only for walking/running legs. All visible
states keep exact values; there is no numeric rounding or timing simplification.
The cloud check compares cached and direct character pixels exactly.

`install_webgl_kit.py` copies/pins the entry point, shared components and capture
helpers. Kit 1.3.2 selects raw + libx264 for new projects, following the completed
T4 checks; NVENC remains selectable. Worker count remains a separate choice.
`render_backend.json` supports:

- `capture_transport`: `auto` (raw for the current kit), `raw`, `jpeg`.
- `video_encoder`: `auto`, `h264_nvenc`, `libx264`.
- `workers`: still 1–8, independently selected. Existing live jobs do not change.

Auto NVENC falls back with a recorded reason if video encoding is unavailable.
Explicit NVENC requests fail. The Three.js renderer still requires NVIDIA;
CPU video encoding does not enable software WebGL rendering. The probe runs once
per render job, not once in each worker. Encoder metadata is saved alongside
the remote job logs; no notebook restart or driver changes are required.

## Evidence and limits, 2026-11-10

The previous eight-worker video completed and downloaded before the optimization
tests. It was retained, not rerendered. After reconnecting, the eight-browser
comparison completed successfully on the T4. The fresh notebook lacked
runtime_memory.py; the client now uploads the complete WebGL helper dependency
set automatically, including runtime_progress.py and frame_cache.py.

| Eight browsers / 120 identical frames total | Wall time including startup |
| --- | ---: |
| JPEG + x264 | 80.064 s |
| Raw RGBA + x264 | 71.506 s |
| Raw RGBA + NVENC | 72.330 s |

Raw/x264 used 10.69% less wall time (1.12x throughput) than JPEG/x264 in this
bounded check. NVENC was only 1.15% slower than raw/x264: treat them as a practical
tie in this sample, not a general encoder ranking. Exact stationary-character
pixels, output frame counts/format/dimensions and decoded transport alignment
passed. These numbers do not establish a full-video speedup. Defaults retain
raw/x264; NVENC support is verified and remains available. Evidence:
assets/acquisition/capture-eight-worker-result.json and outputs/capture-optimization-report.txt.

The completed single-browser test used the same 30 full-HD frames:

| Path | Capture + encoder finish |
| --- | ---: |
| JPEG + x264 | 8.512 s |
| Raw RGBA + x264 | 5.967 s |
| Raw RGBA + NVENC | 8.260 s |

Raw/x264 was 1.43x as fast in that short sample. NVENC worked but was not faster
than raw/x264 there. This does not establish full-video or eight-browser speed.
Eight simultaneous NVENC encoder-only contexts passed. Each output had the
expected 30 frames, resolution and YUV420 format, with no black-frame interval.
Source log: assets/acquisition/capture-optimization-check.log.

`capture_optimization_check.py.parallel_check` is a bounded GPU verification:
eight browsers each process the same 15 frames in each of eight different shots,
comparing JPEG/x264, raw/x264 and raw/NVENC. It verifies exact cached character
pixels, output dimensions/format/frame counts, and cross-path decoded alignment.
This check is complete. Do not repeat it for ordinary videos, and do not
auto-rerender the completed master. New videos reuse the saved capture/cache fixes.

Local checks: `node --test engine/test_capture_transport.mjs
engine/test_toon_state.mjs`, plus the shared kit/handoff/partition/readback tests.

## Native capture, kit 1.4.0

Latest speed target (2026-11-10): user explicitly asks for the same 1:56 video
rendered within five minutes, preferably three, prioritizing actual speed over
worker count. More workers cannot be promised to scale on two CPU cores: the
120-frame async/raw test took 25.672s with one browser, 29.027s with two,
45.266s with four, 76.060s with eight. Use the fastest measured route, not eight
by assumption. New kit 1.4.0 provides caption-only GPU composition, a per-frame
GPU blank guard, native browser H.264 encoding, and compressed batch transport.
The browser's hardware H.264 backend is unavailable; its native software encoder
passed (120 static frames in 1.225s). Do not call this GPU video encoding.
The moving 120-frame native sample captured in 8.973s excluding browser startup;
120 frames, 1080x1920/30, H.264 full-range 8-bit 4:2:0 and no black frames passed.
One browser was faster than two/four on this route. Full-video 3–5 minute timing
is pending a new measured render, not established by that sample.
Current project capture flag: scene_overlay=none (only captions are drawn in 2D),
shadow_cache=true; backend webcodecs / one browser. Do not use this route for
stories with other 2D overlays without adapting their composition. GPU text/fade
composition was checked at 11 timestamps: non-fade RGB RMSE < .014, max 2/255;
fade differs by at most 1/255. Cached shadows matched exactly at 14 points.
Unchanged mixes and fully verified unchanged exports are now reused by content
hash. A real rerender can set force_render=true; cached playback is not a claim
of fresh render speed. Audio/camera/script/code changes invalidate the cache.
The measured full render writes an adjacent .render-time.txt showing whether
three/five minutes were met, including upload/download/file checks. Do not poll
the submitted final render; the detached worker opens the MP4 or error report.


## Native frame ownership correction — kit 1.4.2

The source scene target can be valid while VideoFrame(WebGLCanvas) produces a
black picture. This occurred at five isolated frames in Fake Inspector. The final
all-frame FFmpeg scan rejected that export. Keep that scan unchanged.

browser_frame.mjs checks the actual encoder input through a 40x30 sampled
VideoFrame. The source check finishes first; the composed canvas is then presented,
PIXEL_PACK_BUFFER is unbound and GPU work is finished before the snapshot. The
presentation/snapshot section has no async yield. A blank immutable frame is
closed and the same animation time is rerendered once; a second failure stops
before encoding. Never copy the prior frame or weaken thresholds. Full-HD frame
transport stays inside the browser/native encoder; only a small verification
thumbnail is read, with bounded encoder output upload as before.

Tests: node --test engine/test_browser_frame.mjs. For an observed capture failure,
verify_browser_capture.py PROJECT FRAME_IDS submits a targeted native encode and
checks frame count plus decoded black frames. This is a failure regression tool,
not a benchmark or editorial review required for every video.
