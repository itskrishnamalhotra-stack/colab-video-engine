import test from 'node:test';
import assert from 'node:assert/strict';
import {toonStateKey,upperBodyDrop} from './webgl_kit/toon_state.mjs';
test('the rig and drawing share seated, child and motion offsets',()=>{
 assert.equal(upperBodyDrop({legs:'stand'},{}),0);
 assert.equal(upperBodyDrop({legs:'sit'},{}),210);
 assert.equal(upperBodyDrop({legs:'walk',bob:4},{kid:true}),194);
 assert.equal(upperBodyDrop({legs:'jump'},{kid:true}),130);
});
test('stationary phase does not invalidate identical character artwork',()=>{
 for(const legs of ['stand','sit','jump',undefined])assert.equal(toonStateKey({legs,phase:1,mood:'smug'}),toonStateKey({legs,phase:2,mood:'smug'}));
});
test('walking, running and all visible facial/body changes retain exact values',()=>{
 for(const legs of ['walk','run'])assert.notEqual(toonStateKey({legs,phase:1}),toonStateKey({legs,phase:1.00001}));
 for(const key of ['blink','talk','bob','squash','headTilt','lean'])assert.notEqual(toonStateKey({[key]:.5}),toonStateKey({[key]:.500001}));
 assert.notEqual(toonStateKey({look:[0,0]}),toonStateKey({look:[.00001,0]}));
});
