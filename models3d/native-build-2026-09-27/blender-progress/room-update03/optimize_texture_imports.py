from pathlib import Path
import re,sys
root=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path.cwd()
if not (root/'project.godot').is_file():
 root=Path(__file__).resolve().parent.parent/'quest-native'
if not (root/'project.godot').is_file():raise SystemExit('Pass the Godot project folder as the first argument')
count=0
for p in (root/'assets').rglob('*.jpg.import'):
 s=p.read_text();s=re.sub(r'compress/mode=\d+','compress/mode=1',s);s=re.sub(r'compress/lossy_quality=[\d.]+','compress/lossy_quality=0.92',s);s=s.replace('detect_3d/compress_to=1','detect_3d/compress_to=0');p.write_text(s);count+=1
print('VISUAL_TEXTURE_IMPORTS',count,'quality .92. CPU source JPEG bytes unchanged.')
