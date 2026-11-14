import json,subprocess,tempfile,unittest
from pathlib import Path
from webgl_finalize import finalize,probe
from video_engine import settings

class SavedFrameFinalization(unittest.TestCase):
 def setUp(self):
  folder=Path(settings()['ffmpeg_bin']);self.ffmpeg=str(folder/'ffmpeg.exe');self.ffprobe=str(folder/'ffprobe.exe')
 def make_clip(self,path,count,color='orange'):
  subprocess.run([self.ffmpeg,'-v','error','-y','-f','lavfi','-i',f'color={color}:s=64x64:r=30','-frames:v',str(count),'-c:v','libx264','-pix_fmt','yuv420p',str(path)],check=True)
 def make_audio(self,path,duration):
  subprocess.run([self.ffmpeg,'-v','error','-y','-f','lavfi','-i','sine=frequency=400:sample_rate=48000','-t',str(duration),str(path)],check=True)
 def test_audio_five_milliseconds_shorter_does_not_drop_the_last_frame(self):
  with tempfile.TemporaryDirectory() as directory:
   p=Path(directory);source=p/'worker.mp4';audio=p/'mix.wav';out=p/'final.mp4'
   self.make_clip(source,59);duration=59/30-.005;self.make_audio(audio,duration)
   info,evidence=finalize([source],audio,out,59,duration,(64,64),ffmpeg=self.ffmpeg,ffprobe=self.ffprobe)
   self.assertEqual(evidence['output_frames'],59);self.assertTrue(evidence['video_stream_unchanged']);self.assertEqual(evidence['rendered_new_frames'],0)
   self.assertEqual(evidence['source_video_packet_sha256'],evidence['output_video_packet_sha256'])
   decoded=json.loads(subprocess.check_output([self.ffprobe,'-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=nb_read_frames','-of','json',str(out)],text=True))
   self.assertEqual(int(decoded['streams'][0]['nb_read_frames']),59)
 def test_multiple_saved_segments_are_merged_without_reencoding(self):
  with tempfile.TemporaryDirectory() as directory:
   p=Path(directory);a=p/'a.mp4';b=p/'b.mp4';audio=p/'mix.wav';out=p/'final.mp4'
   self.make_clip(a,31);self.make_clip(b,28,'blue');self.make_audio(audio,59/30-.005)
   _,evidence=finalize([a,b],audio,out,59,59/30-.005,(64,64),ffmpeg=self.ffmpeg,ffprobe=self.ffprobe)
   self.assertEqual(evidence['source_frame_counts'],[31,28]);self.assertEqual(evidence['output_frames'],59)
 def test_incomplete_saved_capture_is_refused_without_rendering(self):
  with tempfile.TemporaryDirectory() as directory:
   p=Path(directory);source=p/'worker.mp4';audio=p/'mix.wav';out=p/'final.mp4'
   self.make_clip(source,58);self.make_audio(audio,59/30)
   with self.assertRaisesRegex(ValueError,'Saved worker segments contain 58 frames'):
    finalize([source],audio,out,59,59/30,(64,64),ffmpeg=self.ffmpeg,ffprobe=self.ffprobe)
   self.assertFalse(out.exists())
if __name__=='__main__':unittest.main()
