# Isolated Kokoro voice-pack experiments

Approved clone video variant (2026-11-15): the user likes the corrected-source
Liam clone and requested a separate version of the recent one-minute video.
Project: projects/the-room-that-remembers-liam. Original Heart project/export
remains preserved. The project narrator.json pins the existing selected
am_liam_clean_1 NPY by SHA-256; it does not re-clone or alter the installed voice
bank. Global narrator defaults remain Heart 1.0 for other projects.

Custom narration uses the cached Colab Python 3.12 CUDA Kokoro environment.
Native synthesis token durations provide its new word clock, without guessed
fallbacks. The same scenes, music and material sound policy are retained; cuts,
captions, radio dialogue and measured Foley are regenerated against that clock.
The target remains 60 seconds. This version permits bounded native pace fitting
(up to 1.15x), recorded in data/narration-report.json; tiny excess can remove
silent outro padding only, never speech. The first attempt was rejected at
60.045s; a regression now covers that 45ms padding case. This is a new narration
version, so it requires a real render with its own captions and action clock,
not a claim of unchanged encoded pictures. No previous final video is replaced.
Audio/render job evidence, not this preparation note, establishes completion.

Shared code: narration_profile.py, cloud_narration.py,
runtime_custom_narration.py and per-project voice checks in video_engine.py.
Use the standard detached audio/render commands. The audio worker uses the host
HTTP-capable interpreter and cloud GPU synthesis; radio EQ and sound tracing
remain standard. Do not bypass the selected voice hash or the final MP4 gates.


Latest voice-reference correction (2026-11-15): the target is the exact original
ElevenLabs Liam - Energetic preview, NOT stock Kokoro am_liam. User wants ordinary
clear/energetic speech as the baseline; story-specific dramatic delivery can be
considered later. The first LAION refs were unsuitable acted performances (one
contained whisper/gasps/panic), despite the correct speaker ID and clean recording.
Do not reuse them as normal narration references or select a sample by duration
alone. runtime_voice_tune.py now defaults to explicitly screened references or
the exact official demo, never blindly to long-references.json. The corrected
Colab T4 sample and reusable packs are saved under
assets/voices/experimental/liam-clean-demo-20261115. result.json records a 5.494s
successful generation run after setup. This uses a short 4.127s official demo and
remains approximate; Inno is one-pass enrollment, not cumulative model training,
and only reads the first 30 seconds. No new model training or production switch
is authorized by the existence of a test result; the user still judges the match.
Heart remains the production default. Preserve prior trial files as historical.


Production defaults stay Heart / af_heart at speed 1.0 until the user explicitly
chooses another narrator. A voice experiment does not alter an existing video,
publish a voice, or establish an exact speaker match.

The 2026-11-15 Liam experiment used the existing authenticated Colab bridge.
An isolated Python 3.12 virtual environment is at
/content/video_engine/voice-lab/venv. It uses torch 2.8.0+cu128,
kokoro 0.9.4 and inno-kokoro commit
099eb0460438bbb31ad547758723333942b88b6f. Inno requires Python below 3.13,
so the notebook's Python 3.13 environment was kept separate.

Use uv venv with /usr/bin/python3.12, then uv pip install with an explicit
--python /content/video_engine/voice-lab/venv/bin/python. Install CUDA torch
from the official cu128 wheel index and inno-kokoro[torch] from its pinned Git
commit. Install the official en_core_web_sm 3.8.0 wheel into that exact venv
before loading KPipeline; automatic spaCy installation may otherwise target
Colab's global interpreter. espeak-ng is the system phonemizer dependency.
All of these are cached for the life of the runtime. No Blender tools are used.

References were found on the internet by exact provider voice ID
TX3LPaxmHKxFdv7VOQHJ. Three demo pages resolved to the same 4.1-second clip;
those were not looped or represented as additional recordings. Longer English
references were found in LAION's public
elevenlabs-v4-five-language-voice-acting dataset, revision
4b24030e508c0e42b49647bddb96598a7aed884b. The downloaded originals are
19.28 and 27.28 seconds. Their individual audio SHA-256 values were checked
against the published reference manifest. Only selected members of one TAR
were read, not the entire dataset. Dataset metadata declares CC BY 4.0;
retain source provenance and attribution separately from any decision about
production use of a particular voice.

runtime_voice_tune.py requires CUDA for both Tuner and KPipeline; it fails
instead of silently moving either model to CPU. It saves float32 NPY packs
of shape [510,1,256], equivalent PyTorch PT packs, and same-text WAV samples.
The arrays are compatible with Kokoro's custom voice-pack input. It is an
approximate cloning/tuning method; compatibility is not proof of resemblance.
Do not retrain or recreate the pack for each video after selecting a usable one.

Remote command:

    /content/video_engine/voice-lab/venv/bin/python -u /content/video_engine/voice-lab/runtime_voice_tune.py --root /content/video_engine/voice-lab

Download and verify the completed experiment:

    python engine/collect_voice_lab.py

Local output: assets/voices/experimental/liam-inno-20261115. result.json retains
reference provenance, pack/sample hashes, GPU device, generation timings and
the unchanged production-default flag. Local cached AI models and experimental
packs are not published to the public runtime repository.

Sources:
- https://github.com/remsky/inno-kokoro
- https://github.com/remsky/inno-kokoro/blob/main/docs/configuration.md
- https://huggingface.co/datasets/laion/elevenlabs-v4-five-language-voice-acting/blob/main/REFERENCE_AUDIO.md

For kokoro-onnx, load a saved NPY with numpy.load and pass the array as voice
to Kokoro.create. Keep this distinct from the built-in am_liam voice: the stock
Kokoro Liam and ElevenLabs Liam are different voices. Do not overwrite the
installed voices-v1.0.bin or label an experimental pack as a built-in voice.
