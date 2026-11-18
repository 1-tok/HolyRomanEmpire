#!/usr/bin/env python3
"""Rhine v013 painterly geographical map review.
Preserve v012 river course and paint additional Rhine floodplain foliage above it.
Use v007 Strasbourg approved painted artwork where available (city on Ill).
No unconstrained collage of concept art. Modern geometry is provisional for 1618.
"""
from pathlib import Path
import sys, json, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageChops, ImageFilter
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from build_rhine_batch001 import px
W,H=3600,4800
OUT=ROOT/'maps/canvas'
SPR=ROOT/'assets/sprites/rivers/rhine-v013'
QA=ROOT/'reports/rhine-v013-painted-floodplain'
for p in (OUT,SPR,QA):p.mkdir(parents=True,exist_ok=True)
base=Image.open(ROOT/'base/base_3600.jpg').convert('RGBA')
assert base.size==(W,H)
river=Image.open(OUT/'rhine-v012-geographic-overlay.png').convert('RGBA')
assert river.size==(W,H)
# Stable geographic cutout and sample river-core exclusion.
rbox=(690,1440,1650,3220)
x0,y0,x1,y1=rbox
arr=np.asarray(river.crop(rbox))
alpha=arr[:,:,3]
core=(alpha>=210)
bank=(alpha>=60)&(~core)
h,w=core.shape
rng=np.random.default_rng(1618)
scenery=Image.new('RGBA',(w,h),(0,0,0,0))
brush=ImageDraw.Draw(scenery,'RGBA')
# Small land-cover motifs are positioned only inside an existing river-bank
# corridor; no new river geometry is fabricated. Never cover river water.
trees=0; reeds=0; willows=0
for i in range(20000):
    x=int(rng.integers(8,w-8));y=int(rng.integers(8,h-8))
    if not bank[y,x] or np.any(core[max(0,y-5):y+6,max(0,x-5):x+6]):
        continue
    if rng.random()<0.60:
        # Woodland canopies: shaded foliage and tiny trunk, from a higher oblique POV.
        rad=int(rng.integers(2,5))
        shade=int(rng.integers(0,35))
        brush.ellipse((x-rad,y-rad-2,x+rad,y+rad-1),
            fill=(43+shade,72+shade,38+shade,215),
            outline=(57+shade,83+shade,41+shade,145),width=1)
        brush.arc((x-rad+1,y-rad-2,x+rad,y+rad-2),175,275,
            fill=(151,159,78,135),width=1)
        trees+=1
    else:
        # Wet meadows, reed tufts. This is scenery, not a floodplain boundary survey.
        brush.line((x,y+2,x,y-2),fill=(88,104,44,125),width=1)
        brush.line((x+1,y+2,x+2,y-1),fill=(157,149,66,145),width=1)
        reeds+=1
# A handful of riverside willow clusters, avoiding water-core pixels.
for i in range(2500):
    x=int(rng.integers(8,w-8));y=int(rng.integers(8,h-8))
    if not bank[y,x] or np.any(core[y-6:y+7,x-6:x+7]):continue
    rr=int(rng.integers(3,7))
    brush.ellipse((x-rr,y-rr,x+rr,y+rr),fill=(74,114,66,110))
    brush.arc((x-rr,y-rr,x+rr,y+rr),10,175,fill=(148,172,92,130),width=2)
    willows+=1
# Alpha composite foliage onto v012 geographic river.
foliage=Image.new('RGBA',(W,H),(0,0,0,0))
foliage.paste(scenery,(x0,y0))
master=Image.alpha_composite(river,foliage)
# Tile ONE canonical painted master (not independently painted sections).
rebuilt=Image.new('RGBA',(W,H),(0,0,0,0))
pieces=[]
for i,ya in enumerate(range(1400,3250,135),1):
    yb=min(3250,ya+135)
    src=master.crop((0,ya,W,yb))
    bb=src.getbbox()
    if bb is None:continue
    tile=src.crop(bb)
    fn=f'rhine-v013-{i:02d}.png'
    tile.save(SPR/fn,optimize=True)
    b=(bb[0],ya+bb[1])
    decoded=Image.open(SPR/fn).convert('RGBA')
    rebuilt.paste(decoded,b)
    pieces.append(dict(file=fn,x=b[0],y=b[1],width=decoded.width,height=decoded.height,sha256=hashlib.sha256((SPR/fn).read_bytes()).hexdigest(),interval=[ya,yb]))
assert not any(z.getbbox() for z in ImageChops.difference(master,rebuilt).split()),'FATAL: tiled river differs from canonical master'
composite=Image.alpha_composite(base,master)
# Use approved Strasbourg v007 painting on top; it remains a distinct Ill-city vignette.
strasbourg=Image.open(OUT/'strasbourg-approved-painted-overlay-007.png').convert('RGBA')
assert strasbourg.size==(W,H)
composite=Image.alpha_composite(composite,strasbourg)
cfg=json.loads((ROOT/'placements/rhine-batch-001.json').read_text())
placed=[]
for entry in cfg['entries']:
    if entry['site']=='Strasbourg':continue
    p=ROOT/entry['asset']
    if not p.exists():continue
    icon=Image.open(p).convert('RGBA')
    icon.thumbnail((105,105),Image.Resampling.LANCZOS)
    xx=round(entry['x'])-icon.width//2;yy=round(entry['y'])-icon.height//2
    composite.alpha_composite(icon,(xx,yy))
    placed.append(dict(site=entry['site'],x=xx,y=yy))
# Additional towns as neutral location marks, not invented artwork.
towns=[
('Cologne',50.94222,6.95778),('Bonn',50.73528,7.10222),
('Andernach',50.439,7.401),('Koblenz',50.3568,7.59366),
('Boppard',50.231,7.589),('Bingen',49.966,7.899),
('Oppenheim',49.851,8.354),('Germersheim',49.222,8.366),
('Gambsheim',48.692,7.885),('La Wantzenau',48.657,7.825),
('Rhinau',48.318,7.707),('Marckolsheim',48.165,7.547),
('Breisach',48.033,7.582),('Neuenburg',47.814,7.561)]
dd=ImageDraw.Draw(composite)
for name,lat,lon in towns:
    x,y=px(lat,lon);x=round(x);y=round(y)
    if not(0<x<W and 0<y<H):continue
    dd.ellipse((x-4,y-4,x+4,y+4),fill=(241,229,194),outline=(72,52,39),width=2)
    dd.text((x+7,y-8),name,fill=(50,37,24),stroke_width=2,stroke_fill=(244,237,213))
full=OUT/'rhine-v013-geographic-painted-full-canvas.jpg'
composite.convert('RGB').save(full,quality=92)
composite.resize((1200,1600),Image.Resampling.LANCZOS).convert('RGB').save(QA/'full-map-preview.jpg',quality=92)
composite.crop((750,1480,1520,3130)).convert('RGB').save(QA/'rhine-corridor-detail.jpg',quality=94)
composite.crop((865,2380,1310,2800)).resize((890,840),Image.Resampling.LANCZOS).convert('RGB').save(QA/'strasbourg-rhine-separation.jpg',quality=95)
master.save(OUT/'rhine-v013-geographic-painted-overlay.png',optimize=True)
report=dict(version='v013',status='FULL MAP VISUAL REVIEW; NOT PRINT OR HISTORICAL APPROVAL',
    canvas_size=[W,H],base='base/base_3600.jpg',
    geographic_source='existing v012 registered Natural Earth 10m geometry',
    original_v012_preserved=True,original_v007_preserved=True,
    render_order=['actual map base','one canonical geographic Rhine painted scenery','approved Strasbourg v007 Ill vignette','4 existing city sprites','location text markers'],
    river_reach_sprite_count=len(pieces),river_seam_check='PASS pixel-exact single-master raster reassembly',
    scenery=dict(trees=trees,reeds=reeds,willows=willows,method='procedural river-bank motifs, do not interpret as actual 1618 land cover'),
    reused_cities=['Strasbourg v007 painting']+[x['site'] for x in placed],
    supplemental_city_labels=[x[0] for x in towns],
    historic_channel_1618_certified=False,
    painted_new_large_format_city_panels_embedded=False,
    reason='Latest ChatGPT-painted standalone artwork is not stored in the GitHub branch and its freely illustrated watercourse does not automatically align with the canonical Rhine geometry.',
    qa_limits=['Visual banks are illustrative and derived from generalized modern river geometry','Actual 1618 braided channels, marshes, city scale and land-cover history need independent QA','Strict seam test applies only between v013 tiles, not to historical accuracy or the separate Ill vignette'],
    print_approval=False,pieces=pieces)
(QA/'qa.json').write_text(json.dumps(report,indent=2)+'\n')
(SPR/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print('v013 rendered actual full map, artwork preserved, verified',len(pieces),'cutout river sprites')
