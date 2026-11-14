import unittest
import numpy as np
from music_mix import SR,settings,prepare,block
class StoryMusic(unittest.TestCase):
 def test_speech_ducks_music_and_silence_recovers_without_muting_it(self):
  policy=settings({});n=SR*6;score=np.full((SR,2),.1,np.float32);voice=np.zeros((n,2),np.float32);voice[:SR*2]=.12
  music,_=block(score,voice,0,n,policy)
  speaking=np.sqrt(np.mean(music[SR:SR*2]**2));gap=np.sqrt(np.mean(music[SR*3:SR*3+SR//2]**2))
  self.assertGreater(gap,speaking*1.25);self.assertGreater(speaking,.04)
 def test_source_analysis_distinguishes_sub_bass_from_phone_audible_music(self):
  t=np.arange(SR)/SR;policy=settings({})
  def tone(hz):return np.repeat(np.sin(2*np.pi*hz*t)[:,None],2,axis=1).astype(np.float32)
  _,bass=prepare(tone(49),policy);_,melody=prepare(tone(587),policy)
  self.assertFalse(bass['source_has_audible_midrange']);self.assertTrue(melody['source_has_audible_midrange'])
 def test_empty_and_silent_music_are_rejected(self):
  for x in (np.zeros((1,2)),np.zeros((SR,2))):
   with self.assertRaises(ValueError):prepare(x,settings({}))
 def test_short_and_chunked_long_form_use_the_same_music_envelope(self):
  policy=settings({});score=np.ones((SR,2),np.float32)*.1;voice=np.zeros((SR*6,2),np.float32);voice[SR//2:SR*3]=.12
  full,_=block(score,voice,0,len(voice),policy);state=None;parts=[]
  for at in range(0,len(voice),SR*2):
   part,state=block(score,voice[at:at+SR*2],at,len(voice),policy,state);parts.append(part)
  np.testing.assert_allclose(full,np.concatenate(parts),atol=1e-12)
 def test_invalid_gain_cannot_overpower_the_narrator(self):
  with self.assertRaises(ValueError):settings({'sound_design':{'music':{'bed_rms_db':-3}}})
if __name__=='__main__':unittest.main()
