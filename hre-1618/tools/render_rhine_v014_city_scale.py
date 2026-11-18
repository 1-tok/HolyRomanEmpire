#!/usr/bin/env python3
"""Rhine v014 full-map composition: coherent settlement scale and actual map geometry.

Uses ONLY repository-native approved art, so it is reproducible by GitHub Actions.
v013 fixed-geography river scenery is retained without changes; Strasbourg's v007
Ill vignette is in a separate layer and existing cities are independently scaled.
Uncommitted newer concept paintings must not be misrepresented as embedded.
"""
from pathlib import Path
import sys, json, hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageChops
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools'))
from build_rhine_batch001 import px
W,H=3600,4800
OUT=R/'maps/canvas'; QA=R/'reports/rhine-v014-city-scale-review'
SPR=R/'assets/sprites/rivers/rhine-v013'
QA.mkdir(parents=True,exist_ok=True)
base=Image.open(R/'base/base_3600.jpg').convert('RGBA')
geo=Image.open(OUT/'rhine-v013-geographic-painted-overlay.png').convert('RGBA')
ill=Image.open(OUT/'strasbourg-approved-painted-overlay-007.png').convert('RGBA')
assert base.size==geo.size==ill.size==(W,H)
cfg=json.loads((R/'placements/rhine-batch-001.json').read_text())
riverqa=json.loads((R/'reports/rhine-v013-painted-floodplain/qa.json').read_text())
# Verify the previously generated river scenery sprites still equal one single master.
recon=Image.new('RGBA',(W,H),(0,0,0,0))
for e in riverqa['pieces']:
    f=SPR/e['file']
    assert hashlib.sha256(f.read_bytes()).hexdigest()==e['sha256']
    tile=Image.open(f).convert('RGBA')
    assert tile.size==(e['width'],e['height'])
    recon.paste(tile,(e['x'],e['y']))
assert not any(b.getbbox() for b in ImageChops.difference(recon,geo).split()),'v013 changed after approval'
composite=Image.alpha_composite(Image.alpha_composite(base,geo),ill)
# Reuse only correct individually identified city artwork and do NOT make another Strasbourg.
# Relative sprite sizes obey spacing in projected map (Worms-Speyer are close).
widths={'Mainz':145,'Worms':118,'Speyer':118,'Basel':145}
citylayer=Image.new('RGBA',(W,H),(0,0,0,0))
sites=[]
for item in cfg['entries']:
    name=item['site']
    if name=='Strasbourg': continue
    path=R/item['asset']
    assert path.is_file(), f'Missing distinct city artwork: {path}'
    im=Image.open(path).convert('RGBA')
    im.thumbnail((widths[name],widths[name]),Image.Resampling.LANCZOS)
    x=round(item['x'])-im.width//2
    y=round(item['y'])-im.height//2
    citylayer.alpha_composite(im,(x,y))
    sites.append(dict(name=name,source=str(path.relative_to(R)),center=[round(item['x'],2),round(item['y'],2)],
        bbox=[x,y,x+im.width,y+im.height],sprite_px=[im.width,im.height],layer='foreground-city',historical_accuracy='review'))
# Protect against multiple major-city sprites with nearly identical footprint.
for i,a in enumerate(sites):
    for b in sites[i+1:]:
        xa,ya,Xa,Ya=a['bbox']; xb,yb,Xb,Yb=b['bbox']
        overlap=max(0,min(Xa,Xb)-max(xa,xb))*max(0,min(Ya,Yb)-max(ya,yb))
        if overlap>0.20*min((Xa-xa)*(Ya-ya),(Xb-xb)*(Yb-yb)):
            raise RuntimeError(f'Large city art overlap requires manual review: {a["name"]}, {b["name"]}')
composite=Image.alpha_composite(composite,citylayer)
# Period/graphic labels: core city and secondary settlement anchors are kept separated
# from large existing city artworks. These are labels, not fabricated city sprites.
towns=[
('Cologne',50.94222,6.95778,'major-pending-unique-art'),
('Bonn',50.73528,7.10222,'town-pending-art'),
('Andernach',50.439,7.401,'town-pending-art'),
('Koblenz',50.3568,7.59366,'major-pending-unique-art'),
('Boppard',50.231,7.589,'town-pending-art'),
('Bingen',49.966,7.899,'town-pending-art'),
('Oppenheim',49.851,8.354,'town-pending-art'),
('Germersheim',49.222,8.366,'town-pending-art'),
('Gambsheim',48.692,7.885,'village-pending-art'),
('La Wantzenau',48.657,7.825,'village-pending-art'),
('Rhinau',48.318,7.707,'village-pending-art'),
('Marckolsheim',48.165,7.547,'town-pending-art'),
('Breisach',48.033,7.582,'fortified-town-pending-art'),
('Neuenburg',47.814,7.561,'town-pending-art')]
label_layer=Image.new('RGBA',(W,H),(0,0,0,0))
d=ImageDraw.Draw(label_layer)
places=[]
for name,lat,lon,role in towns:
    x,y=px(lat,lon); x,y=round(x),round(y)
    if not(0<x<W and 0<y<H):continue
    d.ellipse((x-4,y-4,x+4,y+4),fill=(239,226,189,255),outline=(68,47,37,255),width=2)
    d.text((x+8,y-8),name,fill=(43,32,24,255),stroke_width=2,stroke_fill=(245,237,214,255))
    places.append(dict(name=name,x=x,y=y,role=role))
composite=Image.alpha_composite(composite,label_layer)
composite.convert('RGB').save(OUT/'rhine-v014-full-map-painted-cities-review.jpg',quality=93)
composite.resize((1200,1600),Image.Resampling.LANCZOS).convert('RGB').save(QA/'full-map-1200.jpg',quality=94)
composite.crop((720,1490,1540,3150)).convert('RGB').save(QA/'rhine-cologne-basel-corridor.jpg',quality=94)
composite.crop((850,1930,1430,2420)).resize((1160,980),Image.Resampling.LANCZOS).convert('RGB').save(QA/'mainz-worms-speyer-cities.jpg',quality=95)
composite.crop((865,2390,1330,2810)).resize((930,840),Image.Resampling.LANCZOS).convert('RGB').save(QA/'strasbourg-ill-rhine.jpg',quality=95)
citylayer.save(OUT/'rhine-v014-major-city-sprites-overlay.png',optimize=True)
qa=dict(version='v014',status='MAP-SCALE CITY ART VISUAL REVIEW',base='base/base_3600.jpg',canvas_size=[W,H],
   painted_geographic_scenery='maps/canvas/rhine-v013-geographic-painted-overlay.png',
   historic_rhine_1618_certified=False,
   new_chat_painted_panels_embedded=False,
   source_notes='All placed large city art comes from existing committed independently named city sprites; Strasbourg artwork from v007 Ill-centered overlay.',
   citylayer='maps/canvas/rhine-v014-major-city-sprites-overlay.png',
   map_preview='maps/canvas/rhine-v014-full-map-painted-cities-review.jpg',
   exact_river_sprite_seams='PASS: v013 canonical master equals its 13 native PNG pieces',
   cities=sites,approved_strasbourg_asset='maps/canvas/strasbourg-approved-painted-overlay-007.png',
   supplementary_city_anchors=places,
   historic_warnings=['Do not add completed Cologne cathedral towers before nineteenth century','Do not include Neuwied town (founded 1653) or Neuf-Brisach (founded 1699)','Strasbourg is on the Ill; do not paint main Rhine directly through city',
       'Modern generalized river course does not prove 1618 channels and islands'],
   qa_gate='WAIT for user map-scale review and unique artwork binary intake',print_approval=False)
(QA/'qa.json').write_text(json.dumps(qa,indent=2)+'\n')
print('PASS v014 real 3600x4800: 4 existing city paintings, preserved Strasbourg v007,',len(places),'new settlement markers, exact v013 river tile reconstruction')
