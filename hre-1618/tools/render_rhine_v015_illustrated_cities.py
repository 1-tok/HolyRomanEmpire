#!/usr/bin/env python3
"""Rhine v015 — new differentiated 1618 river-city review sprites on real HRE canvas.

The large unregistered chat illustration panels are NOT asserted to be in GitHub.
This renderer creates actual individual small town/city PNGs with the same
warm watercolor palette and elevated 3/4 viewpoint and places them at the
existing map's Lambert geographic anchors, keeping the existing v013 Rhine.
These are illustrative, not documentary reconstructions of historical walls.
"""
from pathlib import Path
import sys, json, math, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from build_rhine_batch001 import px
W,H=3600,4800
OUT=ROOT/'maps/canvas'; QA=ROOT/'reports/rhine-v015-new-city-sprites'
DEST=ROOT/'assets/sprites/cities/rhine-v015'
for d in (OUT,QA,DEST): d.mkdir(parents=True,exist_ok=True)
base=Image.open(ROOT/'base/base_3600.jpg').convert('RGBA')
rhine=Image.open(OUT/'rhine-v013-geographic-painted-overlay.png').convert('RGBA')
ill=Image.open(OUT/'strasbourg-approved-painted-overlay-007.png').convert('RGBA')
prior=Image.open(OUT/'rhine-v014-major-city-sprites-overlay.png').convert('RGBA')
assert base.size==rhine.size==ill.size==prior.size==(W,H)
# Render previous styles in prescribed layer order. Do not touch original files.
result=Image.alpha_composite(Image.alpha_composite(Image.alpha_composite(base,rhine),ill),prior)
# For historically attested settlements only. Approximate center points in WGS84.
# No Neuwied (post-1618), Neuf-Brisach (post-1618), or finished Cologne cathedral.
records=[
("Cologne",50.94222,6.95778,142,"major","unfinished-gothic"),
("Bonn",50.73528,7.10222,75,"town","church"),
("Andernach",50.439,7.401,38,"walled","church"),
("Koblenz",50.3568,7.59366,118,"major","confluence"),
("Boppard",50.231,7.589,34,"town","church"),
("Bingen",49.966,7.899,77,"walled","church"),
("Oppenheim",49.851,8.354,73,"walled","church"),
("Germersheim",49.222,8.366,73,"walled","church"),
("Gambsheim",48.692,7.885,24,"village","church"),
("La Wantzenau",48.657,7.825,22,"village","church"),
("Rhinau",48.318,7.707,47,"village","church"),
("Marckolsheim",48.165,7.547,38,"walled","church"),
("Breisach",48.033,7.582,104,"walled","hill"),
("Neuenburg",47.814,7.561,63,"town","church"),
]
# Avoid duplicate large sites already present (Mainz, Worms, Speyer, Basel, Strasbourg).
def scene_city(name, size, kind, landmark):
    """Make an oblique, independently transparent painterly town cutout."""
    # Draw at 3x target resolution and downsample for antialiasing.
    scale=3; ww=size*scale; hh=int(size*.78)*scale
    img=Image.new('RGBA',(ww,hh),(0,0,0,0))
    d=ImageDraw.Draw(img,'RGBA')
    import random
    rng=random.Random(sum((i+1)*ord(c) for i,c in enumerate(name)))
    def pp(t):return int(round(t*scale))
    # Soft irregular ground footprint: no hard rectangular artifact.
    footprint=[(0.05,.75),(.14,.60),(.25,.54),(.34,.53),(.47,.49),(.63,.54),(.78,.56),(.91,.68),(.96,.81),(.84,.88),(.25,.91)]
    d.polygon([(pp(x*size),pp(y*(hh/scale))) for x,y in footprint],
        fill=(107,139,74,115))
    def house(cx,cy,rw,rh):
        x=pp(cx);y=pp(cy);w=pp(rw);h=pp(rh)
        # Side from south: front and right side visible, roof ridge leaning northeast.
        d.polygon([(x-w//2,y),(x+w//2,y),(x+w//2,y+h),(x-w//2,y+h)],
            fill=(206+rng.randint(-18,10),192+rng.randint(-20,6),151,255),
            outline=(95,78,59,220))
        d.polygon([(x+w//2,y),(x+w//2+pp(.9),y-pp(1.4)),(x+w//2+pp(.9),y+h-pp(1.4)),(x+w//2,y+h)],
            fill=(151,139,118,240))
        d.polygon([(x-w//2-pp(1),y),(x,y-pp(rh*.65)),(x+w//2+pp(1),y)],
            fill=(135+rng.randint(-20,25),62+rng.randint(-9,12),42,255),
            outline=(88,51,36,245))
        if w>=pp(4):
            d.rectangle([x-pp(.8),y+pp(1),x+pp(.2),y+pp(2.5)], fill=(63,51,43,240))
    number={'major':27,'walled':16,'town':11,'village':6}[kind]
    for k in range(number):
        cx=rng.uniform(size*.23,size*.78)
        cy=rng.uniform(hh/scale*.34,hh/scale*.69)
        house(cx,cy,rng.uniform(3.0,5.2),rng.uniform(3.0,4.6))
    # Fortifications for pre-1618 walled towns.
    if kind in ('major','walled'):
        y=pp(hh/scale*.73)
        d.line([(pp(size*.16),y),(pp(size*.84),y)],fill=(143,133,111,255),width=pp(4))
        d.line([(pp(size*.16),y-pp(2)),(pp(size*.84),y-pp(2))],fill=(224,205,164,255),width=pp(1))
        for frac in (.18,.40,.61,.83):
            x=pp(size*frac)
            d.rectangle((x-pp(2.2),y-pp(8),x+pp(2.2),y+pp(3)),
                        fill=(181,158,123,255),outline=(87,75,62,255),width=1)
            d.polygon([(x-pp(3),y-pp(8)),(x,y-pp(12)),(x+pp(3),y-pp(8))],
                      fill=(119,64,45,255))
    # Period-sensitive dominant church: Cologne keeps unfinished towers.
    lx=pp(size*.53);by=pp(hh/scale*.49)
    body_w=pp(7 if kind!='major' else 10)
    d.rectangle((lx-body_w//2,by-pp(11),lx+body_w//2,by+pp(3)),
                fill=(184,165,133,255),outline=(88,74,54,240))
    if landmark=='unfinished-gothic':
        d.rectangle((lx-pp(2),by-pp(20),lx+pp(1),by-pp(5)),fill=(95,84,70,255))
        # Explicitly no completed cathedral twin spires.
        d.line((lx-pp(1),by-pp(23),lx-pp(1),by-pp(20)),fill=(85,79,66,255),width=pp(1))
    else:
        d.rectangle((lx-pp(2),by-pp(19),lx+pp(2),by-pp(7)),fill=(157,141,112,255))
        d.polygon([(lx-pp(3.5),by-pp(19)),(lx,by-pp(29)),(lx+pp(3.5),by-pp(19))],
                  fill=(94,71,59,255))
    if landmark=='hill':
        d.arc((pp(size*.08),pp(hh/scale*.65),pp(size*.9),pp(hh/scale*.95)),
              180,355,fill=(93,110,65,190),width=pp(2))
    if landmark=='confluence':
        # No invented painted river here; rivers are georeferenced beneath sprite.
        pass
    return img.resize((size,int(size*.78)),Image.Resampling.LANCZOS)

manifest=[]; city_layer=Image.new('RGBA',(W,H),(0,0,0,0))
for name,lat,lon,width,kind,landmark in records:
    x,y=px(lat,lon);x=int(round(x));y=int(round(y))
    if not(0<x<W and 0<y<H):continue
    sprite=scene_city(name,width,kind,landmark)
    path=DEST/(name.lower().replace(' ','-')+'.png')
    sprite.save(path,optimize=True)
    offsets={'Andernach':(-23,-11),'Boppard':(-15,12),'Gambsheim':(12,-12),
             'La Wantzenau':(-12,13),'Marckolsheim':(-16,-9)}
    dx,dy=offsets.get(name,(0,0))
    xx=x-sprite.width//2+dx;yy=y-sprite.height//2+dy
    city_layer.alpha_composite(sprite,(xx,yy))
    manifest.append(dict(name=name,latitude=lat,longitude=lon,anchor=[x,y],
         bbox=[xx,yy,xx+sprite.width,yy+sprite.height],size=[sprite.width,sprite.height],
         file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
         status='illustrative 1618 settlement sprite, historical footprint pending'))
# Reject large overlapping city illustrations while retaining true map anchors.
for i,m in enumerate(manifest):
    ax,ay,AX,AY=m['bbox']
    for n in manifest[i+1:]:
        bx,by,BX,BY=n['bbox']
        area=max(0,min(AX,BX)-max(ax,bx))*max(0,min(AY,BY)-max(ay,by))
        if area > .18*min((AX-ax)*(AY-ay),(BX-bx)*(BY-by)):
            raise RuntimeError('City art overlap requires review: '+m['name']+' / '+n['name'])
assert len({m['sha256'] for m in manifest})==len(manifest)
# Old major centers protected; new city artwork is additive and review-only.
result=Image.alpha_composite(result,city_layer)
# Labels deliberately above painted imagery.
labels=ImageDraw.Draw(result)
for m in manifest:
    x,y=m['anchor']; labels.text((x+7,y+17),m['name'],fill=(47,38,27,255),
       stroke_width=2,stroke_fill=(247,238,206,255))
result.convert('RGB').save(OUT/'rhine-v015-illustrated-settlements-full-map.jpg',quality=94)
result.resize((1200,1600),Image.Resampling.LANCZOS).convert('RGB').save(QA/'full-map-preview.jpg',quality=91)
result.crop((675,1450,1550,3200)).convert('RGB').save(QA/'rhine-illustrated-city-corridor.jpg',quality=95)
result.crop((865,2350,1350,2850)).resize((970,1000),Image.Resampling.LANCZOS).convert('RGB').save(QA/'strasbourg-village-scale.jpg',quality=95)
city_layer.save(OUT/'rhine-v015-new-city-sprites-overlay.png',optimize=True)
qa=dict(batch='v015 river settlement sprite review',canvas_size=[W,H],
    original_v014_preserved=True,original_strasbourg_preserved=True,
    geographical_base='base/base_3600.jpg',
    river_source='maps/canvas/rhine-v013-geographic-painted-overlay.png',
    historic_rhine_course_1618_verified=False,
    new_unique_city_sprites=len(manifest),
    historic_exclusions=['Neuwied (founded 1653)','Neuf-Brisach (founded 1699)','finished Cologne Cathedral towers (19th century)'],
    style='oblique painterly city sketches, distinct source per town; not yet based on new high-resolution standalone chat images',
    source_image_note='Uncommitted stand-alone north/south chat concept paintings are not encoded in repo; this renderer builds native differentiable city sprites for trial placement.',
    approved_original_city_sprites_preserved=['Strasbourg-v007','Basel','Mainz','Speyer','Worms'],
    layer_order=['geographic base','v013 georeferenced wetland and Rhine','v007 Strasbourg Ill','v014 major cities','v015 new city sprites','labels'],
    join_qa='Existing v013 geography retained unaltered. Newly painted cities have feathered transparent grounds; historical riverbank integration still requires inspection.',
    print_approval=False,placements=manifest)
(QA/'qa.json').write_text(json.dumps(qa,indent=2)+'\n')
(DEST/'manifest.json').write_text(json.dumps(qa,indent=2)+'\n')
print('v015 PASS full 3600x4800 actual repo base; new unique city sprites:',len(manifest))
