"""Quick frame validation and cleanup restricted to one worker's owned range."""
import struct
from pathlib import Path

def valid_png(path):
 try:
  with Path(path).open('rb') as stream:
   header=stream.read(24);stream.seek(-12,2);end=stream.read(12)
  return header[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',header[16:24])==(1080,1920) and end==b'\x00\x00\x00\x00IEND\xaeB`\x82'
 except (OSError,ValueError,struct.error):return False

def clean_owned_frames(directory,first,last):
 for frame in range(first,last+1):
  path=Path(directory)/f'frame_{frame:04d}.png'
  if path.is_file() and not valid_png(path):path.unlink()
