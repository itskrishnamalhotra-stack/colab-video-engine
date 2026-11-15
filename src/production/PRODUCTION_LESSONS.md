# Reusable production cautions

These are authoring precautions and shared fixes, not extra production stages.
Use the normal action/sound-state pass, one render and the short technical output
check. Do not add routine previews, contact sheets or editorial approval loops.

## Approved visual and movement benchmark — 2026-11-15

The user approved The Room That Remembers and explicitly requested this standard
for future videos. The completed 60-second example is
`Final Videos/the-room-that-remembers-20261114T225449-da5ab334.mp4`.
Its pictures are identical to the preceding approved full render. The example
scene is `projects/the-room-that-remembers/src/shots.js`; shared implementations
live in `engine/webgl_kit`, not disconnected copies in individual projects.

- Keep the permanent illustrated round-headed character family. Enrich clothes,
  accessories and expressions without replacing its proportions or anatomy.
- Direct motivated camera travel, controlled pans/dollies and varied wide,
  medium, reaction and close-up coverage. Movement must reveal an action, focus
  attention or establish geography; camera motion alone does not replace acting.
- Stage anticipation, body turn, travel, reach, contact, hold and release. Use
  DirectionalActor and pathState: body heading follows travel, front/profile/back
  artwork follows the viewing angle, and walk phase follows actual distance.
- Reuse EntityRegistry character/table/room assemblies and stable furniture,
  wardrobe, lighting and prop identities. Build once and evaluate explicit state
  at each timestamp. See SCENE_ASSEMBLIES.md.
- Keep arms attached at pose-aware shoulders. Reach the prop before attaching it
  to the hand socket; hold it at chest height or beside the face. Keep hands and
  held objects clear of either person's face through the camera move.
- Use frameShot with the intended actors, hands and props. Preserve faces/hats,
  focal objects and caption margins throughout the move. Close-ups retain body
  ownership for acting hands; object-only inserts contain no floating hands.
- Give sets depth and relevant detail; keep light direction and practical effects
  physically readable. Flashlights emit forward from their lens. A story reveal
  changes the actual object or performance, not just a generic flash or zoom.

New stories need their own shot intent, choreography, pacing and sound triggers.
Reuse these components and standard, not this horror story's exact shots, room,
music or cue timestamps. The landscape example does not change a short's requested
portrait format. User approval establishes a benchmark, not an automatic guarantee
of identical creative quality. Do not repin or modify an active render to save rules.

## Failures already fixed in shared code

| Failure / caution | Reusable correction and evidence |
| --- | --- |
| Cloud audio tracing tried the Windows Chrome executable. | cloud_soundtrack.py selects CHROME from cloud tool paths; test_cloud_soundtrack.py covers cloud preparation. Do not copy local executable paths into runtime jobs. |
| Cloud remix lacked referenced footstep03.ogg. | Upload every unique referenced Foley source explicitly; soundtrack_inputs validates paths and existence before submission. A normal render package's finished mix is insufficient for remixing. |
| Identical source files hashed differently on Windows/Linux. | render_reuse.path_order sorts case-folded relative path components consistently. test_render_reuse.py covers cross-platform ordering; never bypass cache/stream checks. |
| Custom narration exceeded 60 seconds by 45 ms after bounded synthesis. | runtime_custom_narration.fit_outro removes excess silent outro padding only, retaining the minimum outro. test_custom_narration.py covers this edge and rejects genuine overflow. Never cut speech or guess word timing to fit. |
| Narrator identity or timing could drift between versions. | narration_profile.py pins each custom voice pack by hash; video_engine.py checks the synthesis report, voice and bounded speed. New narration gets its own measured word/action clock; preserve the original final. The default is now the approved am_liam_clean_1 pack, explicitly selected
  on 2026-11-15; existing project voices are preserved. |
| A correct voice ID still supplied the wrong acted delivery. | runtime_voice_tune.py uses an explicitly selected reference or the exact approved demo, not a longer reference chosen by duration alone. test_voice_reference_policy.py covers selection. Reuse the approved saved pack rather than cloning again per video. |
| spaCy model auto-install targeted the global Colab interpreter. | Install the pinned language-model wheel into the explicit isolated voice-lab Python environment before loading KPipeline. VOICE_EXPERIMENTS.md records the setup; cache it for the runtime lifetime. |
| Complete captured video lost a final frame during muxing. | webgl_finalize.py fits audio to the exact frame clock without -shortest, preserves encoded packets and validates frame counts. Reuse complete retained segments for finalization recovery instead of recapturing by default. |

Keep actual-contact Foley and source-onset alignment, material-matched clean
samples, audible genre-appropriate music and clear narration. The shared
music_mix.py/music_policy.json rule is reusable; a horror score is not a default
for every genre. Audio-only revisions use verified stream-copy when pictures and
their clock are unchanged. A new narration clock can require new capture.

Do not bypass failed timing, cache, frame-count or black-frame gates. A submitted
job is not a finished video. The detached worker owns checks, retrieval and opening;
fix a reported execution failure in shared code where applicable, without turning
ordinary production into a recurring editorial review process.
