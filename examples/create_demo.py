#!/usr/bin/env python3
"""Create synthetic diagrams and a runnable input; never use personal materials."""
from pathlib import Path
import json, subprocess, sys
from PIL import Image, ImageDraw
root=Path(__file__).resolve().parents[1]
work=root/'output';work.mkdir(exist_ok=True)
assets=[]
for n,(name,color) in enumerate([('cover','#e9f2ff'),('page-1','#fff0e4'),('page-2','#e7f5ed')]):
    im=Image.new('RGB',(600,800),color);d=ImageDraw.Draw(im)
    d.rounded_rectangle((35,35,565,765),radius=24,fill='white')
    d.text((75,90),'SYNTHETIC DEMO',fill='#23415d')
    d.text((75,140),name.upper(),fill='#23415d')
    for k in range(3):
        y=240+k*125;d.rounded_rectangle((75,y,525,y+90),radius=12,fill=color)
        d.text((95,y+35),'Idea / review / choose',fill='#23415d')
    path=work/(name+'.png');im.save(path)
    assets.append({'id':name,'label':name,'role':'cover' if n==0 else 'photo','path':str(path.resolve())})
payload=json.loads((root/'examples/workbench-input.json').read_text())
payload['covers']=assets[:1];payload['photos']=assets[1:]
payload['titles'].append({'id':'title-2','label':'A fresh angle','text':'街角也有新发现'})
payload['body_variants'].append({'id':'body-2','label':'Short version','text':'示例文案：整理图片，选择标题，再检查发布顺序。'})
p=(work/'demo-input.json');p.write_text(json.dumps(payload,ensure_ascii=False,indent=2))
subprocess.run([sys.executable,str(root/'scripts/validate_workbench.py'),'--input',str(p)],check=True)
subprocess.run([sys.executable,str(root/'scripts/build_workbench.py'),'--input',str(p),'--output',str(work/'demo.html')],check=True)
print('Open output/demo.html locally. Generated files are private and ignored by Git.')
