# Isolated Kokoro voice-pack experiments

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
