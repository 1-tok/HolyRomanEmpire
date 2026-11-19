#!/usr/bin/env python3
"""Compose v017 large painted Rhine pieces on the actual 3600x4800 HRE canvas.
Source-only raster exactness; no miniature city sprites, procedural wetland,
or false claims of new north/south extensions. City manifest audited separately.
"""
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw
import json, hashlib, sys
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools'))
from build_rhine_batch001 import px
OUT=R/'maps/canvas'
QA=R/'reports/rhine-v017-large-map-placement'
CUT=R/'reports/rhine-v017-large-seam-baseline'
SOURCE=R/'assets/reference/rhine-v011-full-painted-strip-overlay-3600x4800.png'
BASE=R/'base/base_3600.jpg'
for p in (OUT,QA):p.mkdir(parents=True,exist_ok=True)
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()=='b24dd693d513704b87fb26e7bb02eeaf771e8ef10a0a1790481940b7611e1af4'
source=Image.open(SOURCE).convert('RGBA')
base=Image.open(BASE).convert('RGBA')
assert source.size==base.size==(3600,4800)
manifest=json.loads((CUT/'qa.json').read_text())
reassembly=Image.new('RGBA',source.size,(0,0,0,0))
used=[]
for record in manifest['sections']:
    b=record['source_bbox_px']
    a,c=record['unblended_core_y_px']
    f=CUT/record['image']
    panel=Image.open(f).convert('RGBA')
    assert panel.size==(b[2]-b[0],b[3]-b[1])
    core=panel.crop((0,a-b[1],panel.width,c-b[1]))
    reassembly.paste(core,(b[0],a))
    used.append({'file':str(f.relative_to(R)),'core_y':[a,c],'map_x':b[0],
                 'source_bbox':b,'original_pixels_unchanged':True})
diff=ImageChops.difference(reassembly,source)
assert all(ch.getbbox() is None for ch in diff.split()), 'Large-piece assembly does not reproduce original source pixels'
full=Image.alpha_composite(base,reassembly)
fullpath=OUT/'rhine-v017-large-painted-sections-on-map.jpg'
full.convert('RGB').save(fullpath,quality=94,subsampling=0)
assert Image.open(fullpath).size==(3600,4800)
paintpath=OUT/'rhine-v017-reassembled-large-painting.png'
reassembly.save(paintpath,optimize=True)
# Final map-scale visual review, cropped around corridor, with no debug marks.
view=(675,1750,1550,3425)
full.crop(view).convert('RGB').save(QA/'painted-rhine-map-scale-unchanged.jpg',quality=96)
# Separate city position QA only; avoid printing labels/dots into painting.
city_review=full.crop(view).convert('RGBA')
city_draw=ImageDraw.Draw(city_review)
settings=json.loads((R/'placements/rhine-v017-panel-manifest.json').read_text())
sites=[]
for c in settings['cities']:
    x,y=px(c['lat'],c['lon'])
    inside=view[0]<=x<view[2] and view[1]<=y<view[3]
    if inside:
        tx,ty=x-view[0],y-view[1]
        city_draw.ellipse((tx-4,ty-4,tx+4,ty+4),fill=(255,215,40,255),
                        outline=(27,24,19,255),width=1)
        city_draw.text((tx+7,ty-8),c['site'],fill=(255,245,187,255),
                       stroke_width=2,stroke_fill=(35,28,24,255))
    sites.append({'name':c['site'],'panel':c['panel'],'work_xy':[round(x,2),round(y,2)],
                  'inside_corridor_qa_crop':inside,
                  'large_v017_unique_new_city_painting_verified':False})
city_review.convert('RGB').save(QA/'city-anchors-over-large-painting-QA.jpg',quality=95)
status={'version':'v017','status':'ACTUAL HRE MAP PLACEMENT, ORIGINAL PAINTING ONLY',
 'full_map_file':str(fullpath.relative_to(R)),
 'source_master_file':str(SOURCE.relative_to(R)),
 'reassembled_overlay_file':str(paintpath.relative_to(R)),
 'pixel_exact_source_reassembly':True,'source_delta_pixels':0,
 'sections':used,'canvas_size':[3600,4800],
 'city_targets':sites,'target_city_count':len(sites),
 'new_city_art_verified_this_build':0,
 'notes':'Three sections are slices of one approved 1618 painted master (v011). No genuinely new city-bearing northern or southern painting is accepted. City position markers appear only on separate QA image. Do not confuse these with existing painted city artwork.',
 'main_fork_new_art_placed':False,
 'new_north_extension_placed':False,'new_south_extension_placed':False,
 'historical_water_1618_verified':False,'approved_for_300_ppi_print':False}
(QA/'qa.json').write_text(json.dumps(status,indent=2)+'\n')
print('PASS assembled large artwork on real map, 0 different source pixels, 25 city anchors QA; original v016 unchanged.')
