"""Word-clock ASS captions shared by the WebGL runtime."""
import json
from pathlib import Path
def ass_time(t):
    cs=max(0,round(t*100));h,cs=divmod(cs,360000);m,cs=divmod(cs,6000);s,cs=divmod(cs,100)
    return f'{h}:{m:02d}:{s:02d}.{cs:02d}'

def make_captions(project):
    words=json.loads((project/'data/words.json').read_text(encoding='utf-8-sig'))
    from video_format import project_dimensions
    width,height=project_dimensions(project)
    header='''[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Inter,52,&H00FFFFFF,&H00FFFFFF,&H00141414,&H80000000,-1,0,0,0,100,100,0,0,1,3,1,2,65,65,420,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    header=header.replace('PlayResX: 1080',f'PlayResX: {width}').replace('PlayResY: 1920',f'PlayResY: {height}')
    if width>height:header=header.replace('65,65,420,1','65,65,96,1')
    rows=[]
    for i,w in enumerate(words):
        start=max(0,float(w['s'])-.025)
        end=float(words[i+1]['s'])-.025 if i+1<len(words) else float(w['e'])+.3
        end=min(end,float(w['e'])+.3)
        if end<=start:continue
        text=w['w'].replace('\\','').replace('{','').replace('}','').replace('\n',' ')
        rows.append(f'Dialogue: 0,{ass_time(start)},{ass_time(end)},Default,,0,0,0,,{text}')
    path=project/'data/captions.ass';path.write_text(header+'\n'.join(rows),encoding='utf-8')
    return path
