# Long-form stories in the approved cartoon family

Use the same visual, narration, exact-contact sound and technical standards as
short videos. A longer runtime is not permission to fill minutes with frozen
actors, wide shots, repeated camera zooms or vague narration.

Direction supplies a concrete hook, identifiable cast, connected cause/effect,
new evidence, consequential decisions, tested solutions and a final payoff.
The story must still work without a film name. Write original narration and give
each visible beat an actual action or reaction, not merely a location change.

The selected saved custom narrator is am_liam_clean_1 at base speed 1.0. For long
stories, duration_policy=natural treats target_duration as an upper bound; the
measured speech, authored gaps and short outro determine actual length, rounded
up to the video frame clock. Do not pad a shorter story to the maximum duration.
Fixed-duration experiments retain their existing policy. Native word timings
drive captions, quoted radio treatment, shot anchors and measured action events.

Keep the approved illustrated round heads, connected arms and tailored wardrobe.
EntityRegistry defines complete persistent characters, furniture groups and rooms.
DirectionalActor/pathState supply travel heading and distance-based walking.
Use the same look definition for a character and any in-story monitor portrait.
Props have an explicit home or hand-socket owner. A transfer reaches a meeting
point before changing owner. Neither a cut nor a close-up removes a body part.

Alternate geography, performance, reactions, evidence inserts and tracking shots
according to story intent. Required framing subjects are the shot's actual focus,
not every background silhouette. Keep the background cast physically present;
do not hide characters to fake coverage. Main evidence shots protect all intended
faces and objects. Patient/trolley coverage includes the complete trolley assembly;
place pushers behind the handle with clear separation from the patient's head.
Use frameShot; never disable a failed face, cropping or black-frame gate.

The reusable hospital modules are hospital.js, hospital_props.js,
hospital_continuity.js, hospital_coverage.js and hospital_performance.js. The
performance vocabulary has a particular hospital story's beat/role mapping;
another story must author its own mapping, choreography and sound triggers.
EntityRegistry, directional motion, props and camera contracts are independent
components, not a claim that a copied shot list directs a new story automatically.

For projects with cloud_prepare=true and audio_execution=colab, cloud_prepare.py
uploads authored source, the actual narration and every referenced Foley sample.
The existing CPU action/sound-state pass and bounded-memory long-form mix execute
on Colab. A short original score source loops under story-specific dynamics and
speech ducking; quiet beats can deliberately suppress music. Meaningful physical
contacts use relevant licensed samples at their measured output frames. No
guessed contact clock or substitute scratching effects are allowed.

The normal sound-state pass also checks continuity and camera contracts; it is
not an additional editorial review. Reuse a valid trace/mix by content hash.
Then submit one detached final WebGL capture. The worker retrieves the checked
MP4 and same-name publishing JSON into Final Videos, opens success or a readable
failure report, and preserves earlier approved exports. Do not idle-poll capture.

Current rebuilt production: projects/the-voice-on-channel-three-rebuilt,
2258 words, 784.167 seconds, 197 planned shots. This is a new version authorized
on 2026-11-15; the original long project and finals remain unchanged. Preparation
or completed narration does not establish final capture completion or approval.
