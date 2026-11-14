import unittest
from animation_events import bind_events

class MeasuredContactTests(unittest.TestCase):
 def setUp(self):
  self.event={'shot':'s','id':'close','frame':31,'t':31/30,'material':'leather','evidence':{'detector':'rising'}}
  self.trace={'fps':30,'events':[self.event],'observations':[]}
  self.binding={'shot':'s','event':'close','sample':'handleSmallLeather.ogg','material':'leather','reason':'Wallet flap closes.'}
 def test_exact_frame_and_audible_onset_are_carried_to_mixer(self):
  cue=bind_events({'events':[self.binding]},self.trace)[0]
  self.assertEqual(cue['frame'],31);self.assertEqual(cue['t'],31/30)
  self.assertTrue(cue['onset_align']);self.assertEqual(cue['timing_source'],'animation-state')
 def test_estimates_offsets_and_wrong_materials_are_rejected(self):
  for key,value in [('at',.5),('repeat_seconds',.4),('offset',-.1),('span',.2),('material','paper')]:
   with self.subTest(key=key),self.assertRaises(ValueError):
    bind_events({'events':[{**self.binding,key:value}]},self.trace)
 def test_missing_event_never_falls_back_to_word_or_fraction(self):
  with self.assertRaisesRegex(ValueError,'No measured animation event'):
   bind_events({'events':[{**self.binding,'event':'missing'}]},self.trace)
 def test_a_correct_timestamp_does_not_allow_an_unrelated_sample(self):
  with self.assertRaisesRegex(ValueError,'not approved for this material'):
   bind_events({'events':[{**self.binding,'sample':'bookPlace1.ogg'}]},self.trace)
 def test_a_short_shot_without_a_foot_landing_emits_no_fake_step(self):
  trace={**self.trace,'events':[],'observations':[{'shot':'s','id':'close','min_events':0}]}
  self.assertEqual(bind_events({'events':[self.binding]},trace),[])

if __name__=='__main__':unittest.main()
