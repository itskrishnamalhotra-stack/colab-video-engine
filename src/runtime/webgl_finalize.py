"""Finalize saved WebGL segments without rendering any animation frames."""
import hashlib,json,os,re,subprocess
from pathlib import Path

def probe(path,ffprobe='ffprobe'):
 return json.loads(subprocess.check_output([ffprobe,'-v','error','-show_streams','-show_format','-of','json',str(path)],text=True))

def packet_hash(arguments,ffmpeg='ffmpeg'):
 # Hash compressed video packets, not decoded/re-encoded pictures or the MP4 container.
 text=subprocess.check_output([ffmpeg,'-v','error',*arguments,'-map','0:v:0','-c:v','copy','-bsf:v','h264_mp4toannexb','-f','hash','-hash','sha256','-'],text=True)
 return text.strip().split('=',1)[1]

def soundtrack_clock(total):
 if not isinstance(total,int) or total<=0:raise ValueError('A positive video frame count is required')
 samples=total*1600
 return f'aresample=48000,apad=whole_len={samples},atrim=end_sample={samples}'

def finalize(segments,mix,output,total,expected,dimensions,progress=None,ffmpeg='ffmpeg',ffprobe='ffprobe'):
 segments=[Path(p).resolve(strict=True) for p in segments];output=Path(output);mix=Path(mix).resolve(strict=True)
 if not segments or total<=0:raise ValueError('No completed WebGL frames to finalize')
 counts=[]
 for path in segments:
  info=probe(path,ffprobe);video=next(s for s in info['streams'] if s['codec_type']=='video')
  count=int(video.get('nb_frames',0));counts.append(count)
  if count<=0 or (video['width'],video['height'])!=tuple(dimensions) or video.get('codec_name')!='h264':
   raise ValueError('Saved worker segment is incomplete or has the wrong format: '+str(path))
 if sum(counts)!=total:raise ValueError(f'Saved worker segments contain {sum(counts)} frames; expected {total}. No render or final-gate bypass was attempted.')
 audio_info=probe(mix,ffprobe);audio_seconds=float(audio_info['format']['duration'])
 if abs(audio_seconds-expected)>.10:raise ValueError('Prepared narration mix has the wrong duration')
 output.parent.mkdir(parents=True,exist_ok=True)
 concat=output.with_suffix('.segments.txt')
 concat.write_text(''.join("file '"+str(path).replace('\\','/').replace("'","'\\''")+"'\n" for path in segments),encoding='utf-8')
 temporary=output.with_name(output.stem+'.partial.mp4')
 inputs=['-f','concat','-safe','0','-i',str(concat)]
 if progress:progress('encoding_mp4')
 # Quantize only the soundtrack's existing final silence to the video frame
 # clock. -shortest can discard the last copied video packet for a sub-frame
 # audio difference; never use it here. 48 kHz / 30 fps = 1600 samples/frame.
 samples=total*1600
 subprocess.run([ffmpeg,'-v','error','-y',*inputs,'-i',str(mix),'-map','0:v:0','-map','1:a:0',
  '-c:v','copy','-af',soundtrack_clock(total),
  '-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart',str(temporary)],check=True)
 if progress:progress('checking_mp4')
 info=probe(temporary,ffprobe);video=next(s for s in info['streams'] if s['codec_type']=='video')
 if (video['width'],video['height'])!=tuple(dimensions) or not any(s['codec_type']=='audio' for s in info['streams']):raise ValueError('Output needs the declared full-HD format and narration audio.')
 if video.get('codec_name')!='h264' or video.get('pix_fmt') not in ('yuv420p','yuvj420p'):raise ValueError('Output must remain 8-bit H.264 / YUV420.')
 if video.get('pix_fmt')=='yuvj420p' and video.get('color_range')!='pc':raise ValueError('Full-range YUV420 must retain its correct range metadata.')
 if abs(float(info['format']['duration'])-expected)>.25:raise ValueError('Incorrect rendered duration.')
 if int(video.get('nb_frames',0))!=total:raise ValueError(f"Worker merge lost or duplicated video frames: {video.get('nb_frames')} / {total}.")
 before=packet_hash(inputs,ffmpeg);after=packet_hash(['-i',str(temporary)],ffmpeg)
 if before!=after:raise ValueError('Finalization changed compressed video packets; refusing delivery.')
 scan=subprocess.run([ffmpeg,'-hide_banner','-nostats','-i',str(temporary),'-vf','blackdetect=d=0.01:pix_th=0.025:pic_th=0.98','-an','-f','null','-'],capture_output=True,text=True,check=True)
 output.with_suffix('.black-frame-check.log').write_text(scan.stderr,encoding='utf-8')
 bad=[(float(a),float(b)) for a,b in re.findall(r'black_start:([\d.]+) black_end:([\d.]+)',scan.stderr) if float(a)>.3 and float(a)<expected-.5]
 if bad:raise ValueError(f'Black-frame flicker detected after rendering: {bad[:8]}. Refusing delivery.')
 os.replace(temporary,output)
 output.with_suffix('.verification.json').write_text(json.dumps(info,indent=2))
 evidence={'source_segments':[str(p) for p in segments],'source_frame_counts':counts,'output_frames':int(video['nb_frames']),
  'source_video_packet_sha256':before,'output_video_packet_sha256':after,'video_stream_unchanged':True,
  'rendered_new_frames':0,'audio_samples':samples,'black_frame_gate':'passed'}
 output.with_suffix('.finalization.json').write_text(json.dumps(evidence,indent=2))
 print('WEBGL_FINALIZED',json.dumps(evidence),flush=True)
 return info,evidence
