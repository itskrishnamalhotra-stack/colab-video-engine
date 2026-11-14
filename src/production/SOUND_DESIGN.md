# Frame-bound sound design

Reusable music rule (2026-11-15): Music must be present and audible on phone
speakers, with a story/genre-specific original or licensed instrumental source.
Avoid a sub-bass-only bed. Use shared music_mix.py / music_policy.json in both
short and long-form mixers: baseline -24 dB RMS before mastering, 4 dB speech
duck, 60ms attack and 650ms release, smooth entrance/exit, and a restrained rise
between phrases. These are starting levels, not a claim of perfect aesthetics;
keep narration and meaningful measured Foley clear. Report source midrange and
actual stem levels. The current horror uses original suspense-phone-v2.wav;
do not reuse this horror score in unrelated genres. Retain material-matched,
measured-contact Foley. Sound-only updates copy verified picture packets and
never rerender animation; audio_execution=colab mixes/finalizes on the connected
runtime. Preserve the approved source export and enforce unchanged-stream and
final MP4 gates. Voice research/samples do not change permanent Heart 1.0 until
the user selects another narrator.


Approved sound standard (user approval, 2026-11-10): the user loves the
measured-contact soundtrack in outputs/pickpocket-webgl-extended-20261110T174404-4b264108.mp4
and wants this approach reused for all future video formats. This job completed
successfully with the encoded video stream verified unchanged. Preserve clean,
relevant material sounds, actual action-frame synchronization, source-onset
alignment, clear fixed Heart narration and ducked suitable music. Do not copy the
same cue positions or pickpocket effects into unrelated stories. New stories
still need authored action observations and relevant sources; another rig/backend
needs an exact timing adapter rather than an estimated fallback. Shared code
reuses tracing, validation, mixing, source policy and audio-only remux. The current
WebGL reference-cartoon path enforces this in code; other formats must apply the
same standard through their own action clock. User approval establishes a quality
benchmark, not a promise that every future creative result is automatically perfect.


The user rejected knife/file rasps and guessed sound positions. Current production
reference cartoons require action_plan.json version 2. Version 1 shot-percentage
Foley is refused for projects with visual_profile.json.

## Action and material first

Use a relevant recorded source for a real visible action. A knife scrape is not
a substitute for pen writing or key filing. Do not add coin jingles to static
coins, footsteps to standing actors, page flips to still paper, or prop impacts
where nothing lands. If a suitable clean recording is unavailable, leave that
physical action quiet under the music rather than inventing a contact.

sound_defaults.json / clean-contact-v1 bans this bank's knife/file rasps, rough
cloth family and added creak textures. sound_materials.json explicitly maps
approved source files to materials. New sources require free license evidence,
a relevant material mapping and an authored action reason, not a filename guess.
Known library sources/credits remain under assets/audio-library.

## Reusable measured timing

1. Author shot word anchors in action_plan.json. The same resolved shot_timing.json
   remains the animation clock. Shot anchors can place cuts; they cannot position
   an effect by a guessed percentage.
2. Author action_probe.json with the story module, one unique observation hook,
   and named property observations. Observe actual parent/visibility changes,
   shoe lifted-to-grounded transitions, insertion/rotation settling, or hinge
   motion. A sound binding references a shot plus event ID, material, source and
   reason. No at, repeat_seconds, until, span, offset or explicit t is accepted.
3. action_sound.py resolves the shots, then animation_events.py runs/reuses the
   CPU-only trace_action_events.mjs scene-state pass. The pass executes the actual
   story act/reset/camera functions at every output frame, using the capture's
   rounded frame count and frame/fps clock. It does not create a WebGL context or
   render images. Original production source files are unchanged; an observation
   hook is inserted only in the local HTTP response. The existing puppet adapter
   omits canvas painting and reads the foot lift expression from the pinned
   drawing source, including each actor's actual phase. It does not use a separate
   approximate footstep cadence. Other rigs need their own exact adapter.
4. action_event_trace.mjs records state edges and evidence. Settling is stamped
   on the first frame at rest, confirmed by the next frame. Already-grounded feet
   or props already held at a cut do not create fake contacts. Motion beginning
   on the first shot frame can use an explicitly authored rest-state baseline.
   Short shots with no foot landing emit no step. Required missing events fail;
   there is no guessed-time fallback.
5. data/animation-events.json is bound to the visual-source/probe/adapter hashes,
   with an internal content hash. Changed scene/timing/probe code reruns the pass.
   data/sound-sync-audit.md lists frame, time, source, material and reason, plus
   deliberately silent actions. Frame numbers are zero-based.
6. foley_mix.py checks that cues equal the measured event bindings. It trims
   leading source silence to the first detectable attack (-40 dB relative to
   that sample's peak), then places that attack on frame/fps. At 30 fps and 48 kHz
   this is exactly 1600 audio samples per frame. sound-report.json records the
   placed audio sample and removed leading samples. Precision is the rendered
   frame (33.3 ms), not subframe physics or a claim that a state audit proves
   perfect collision geometry or artistic sound quality.

Current adapter/example: engine/author_pickpocket_contacts.py and
projects/pickpocket-webgl-extended/action_probe.json. The 116.034-second story
contains 3481 output frames, 53 shots and 39 measured sound events in this revision.
Old 99/140 cue counts describe superseded mixes, not approved precision.

## Mix and delivery

Preserve Heart af_heart at speed 1.0 and the approved cartoon pictures. Music and
relevant effects remain required unless waived. Music ducks under narration.
The recorded mixer controls crest peaks and event RMS, with a -4 dB event peak
ceiling; the final master targets -16 LUFS / -1.5 dBTP. Short, clean paper/leather
sounds are preferable to noisy friction beds. Cue count is not a quality score.

Use python engine/video_engine.py remux projects/NAME for sound-only changes.
This detached job preserves the verified encoded picture stream, compares its
SHA-256 before/after, checks the final MP4 and opens it. No Colab or GPU render is
needed. New animation/shot timing requires a normal full render.

Relevant checks: test_action_event_trace.mjs, test_animation_events.py,
test_action_sound.py, test_foley_mix.py, test_sound_profile.py, test_render_reuse.py.
New stories still require their own staging, meaningful action observations and
appropriate sample choices. Reuse the implementation; do not copy the pickpocket
plot or quietly revive percentage cue timing.
