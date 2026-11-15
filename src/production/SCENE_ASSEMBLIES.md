# Persistent cartoon assemblies

The illustrated character family is permanent. Use DirectionalActor to enhance
the existing Toon artwork, not to substitute another character model.

Define each entity once with EntityRegistry. Spawn it once, then retrieve that
same object in every shot. A character factory stores its full look, palette,
hat, clothing detail, accessories and named hand sockets. A table factory owns
its complete contents. A room factory owns furniture, fixtures and stable lights.

```js
registry.define('mc', {
  factory: () => new DirectionalActor(room.root, {
    id: 'mc', coat: '#718B7D', hat: '#374F60',
    look: {hat: 'beanie', pattern: 'trench', neck: 'collar',
           detail: 'tailored', extra: []}
  }),
  required: ['character_body', 'wardrobe_and_face', 'mc.l_grip', 'mc.r_grip']
});
const mc = await registry.spawn('mc');
const sameCharacter = registry.get('mc');
const rightHand = registry.get('mc', 'mc.r_grip');
```

Use pathState for travel heading and a turn before translation. Call actor.face
with the shot camera to choose front/profile/back artwork from that heading.
Looking at something is separate from moving toward it. Do not show front art
while the actor is walking away. Directional views retain the same wardrobe.

Stage the physical reach, then transfer the same prop to a named hand socket.
Keep a held object at chest height or to the side of the face. Do not animate
individual fingers unless they are essential to the shot. Return the same prop
to its named home for deterministic random-access scene evaluation.

Close-ups change camera coverage, never body visibility. Keep connected body
context when hands act; an object-only insert must exclude unrelated hands.
Fit intended heads and focus objects through the camera move with frameShot.

The normal action_probe sound-state pass calls registry.assertContinuity and
actor.assertIntact. A required part missing, hidden or detached is an error.
Explicit prop transfers may change parent but must retain identity and stay in
the same scene. Store room geography and reject accidental layout changes.
No separate routine editorial pass is added. Investigate user-reported faults
directly, render once and apply normal technical completion checks.

Working example: projects/the-room-that-remembers/src/shots.js and
scene_manifest.json. It has mc, center_table and main_room, directional walking,
an actual reach/pickup, hand-held radio, stable room coverage and measured Foley.
The user approved its completed animation on 2026-11-15 as the camera/body-motion
and continuity benchmark for future videos. See PRODUCTION_LESSONS.md for the
authoring standard and reusable failure corrections; no extra review stage.
