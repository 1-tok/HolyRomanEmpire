#!/usr/bin/env python3
"""Rhine v016 vs georeferenced Rhine course: map-scale alignment audit.

This tests whether pixels that resemble painted BLUE WATER follow existing
geographic centerline geometry. It does NOT certify AD 1618 channel positions.
"""
import json, math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import distance_transform_edt, binary_dilation
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/rhine-v016-geography-audit'
OUT.mkdir(parents=True,exist_ok=True)
painting=Image.open(ROOT/'assets/reference/rhine-v011-full-painted-strip-overlay-3600x4800.png').convert('RGBA')
canonical=Image.open(ROOT/'maps/canvas/rhine-v012-geographic-overlay.png').convert('RGBA')
assert painting.size==canonical.size==(3600,4800)
limits=(750,1870,1345,3310)
x0,y0,x1,y1=limits
P=np.asarray(painting.crop(limits),dtype=np.int16)
G=np.asarray(canonical.crop(limits),dtype=np.int16)
# Color classifier is consciously conservative: dark blueish water visible, opaque art.
paintwater=(P[:,:,3]>110)&(P[:,:,2]>=P[:,:,0]+5)&(P[:,:,1]>=P[:,:,0]+2)&(P[:,:,1]>75)
# For geographic v012 main water is alpha >= 210 and clearly blue-toned.
geowater=(G[:,:,3]>210)&(G[:,:,2]>G[:,:,0]+16)&(G[:,:,1]>G[:,:,0]+18)
# Avoid river course empty values, and limit to the region of actually painted pixels.
distance=distance_transform_edt(~paintwater)
backdist=distance_transform_edt(~geowater)
bands=[
('north_mainz',1900,2100),
('worms_speyer',2100,2350),
('north_strasbourg',2350,2490),
('strasbourg_ill',2490,2650),
('south_strasbourg',2650,2850),
('breisach_basel',2850,3050),
('south_extension',3050,3274),
]
rows=[]
for name,ya,yb in bands:
    a=max(0,ya-y0); b=min(y1-y0,yb-y0)
    relevant_geo=geowater[a:b]
    relevant_paint=paintwater[a:b]
    gy,gx=np.where(relevant_geo)
    py,px=np.where(relevant_paint)
    n=int(len(gx))
    values=distance[a:b][relevant_geo]
    inverse=backdist[a:b][relevant_paint]
    # mean gap from geographic water pixels to painted blue pixels.
    row=dict(band=name,interval=[ya,yb],
             geographic_water_pixels=n,painted_waterlike_pixels=int(len(px)),
             median_distance_geo_to_paint_px=round(float(np.median(values)),2) if n else None,
             p90_distance_geo_to_paint_px=round(float(np.percentile(values,90)),2) if n else None,
             geographic_water_within_12px_of_paint_fraction=round(float((values<=12).mean()),3) if n else None,
             geographic_water_within_24px_of_paint_fraction=round(float((values<=24).mean()),3) if n else None,
             painted_water_within_24px_of_geographic_fraction=round(float((inverse<=24).mean()),3) if len(px) else None)
    rows.append(row)
# Mainline x center per row and drift to nearest painting blue pixel.
sample=[]
for map_y in range(1920,3250,45):
    y=map_y-y0
    if not (0<=y<geowater.shape[0]):continue
    xs=np.where(geowater[y])[0]
    p_xs=np.where(paintwater[y])[0]
    if len(xs)<3:continue
    geo_mid=int(np.median(xs))+x0
    if len(p_xs)<3:
        nearest_x=None; gap=None
    else:
        nearest_x=int(p_xs[np.argmin(np.abs(p_xs-(geo_mid-x0)))])+x0
        gap=abs(nearest_x-geo_mid)
    sample.append(dict(map_y=map_y,rhine_center_x=geo_mid,nearest_painted_blue_x=nearest_x,delta_px=gap))
# Create honest before/after geographic diagnostic: purple geographic river pixels on top
# of original painting, not mixed into print master.
preview=painting.crop(limits).convert('RGBA')
ann=np.asarray(preview).copy()
outline=binary_dilation(geowater,iterations=2) & ~geowater
ann[outline]=np.array([238,24,191,255],dtype=np.uint8)
# Put a lower-opacity red overlay on existing geographic water
pix=ann[geowater].astype(float)
ann[geowater,:3]=(0.45*pix[:,:3]+0.55*np.array([228,30,185])).astype(np.uint8)
ann[geowater,3]=255
Image.fromarray(ann,'RGBA').convert('RGB').save(OUT/'original-painting-with-registered-rhine-overlay.jpg',quality=94)
# Individual town anchors on a distinct diagnostic.
diagnostic=Image.fromarray(ann,'RGBA')
d=ImageDraw.Draw(diagnostic)
sites=[('Mainz',1185,2003),('Worms',1205,2150),('Speyer',1220,2275),
 ('Strasbourg (Ill)',1032,2563),('Breisach',979,2776),('Basel',973,2964)]
for name,x,y in sites:
    lx=x-x0;ly=y-y0
    d.ellipse((lx-5,ly-5,lx+5,ly+5),fill=(244,217,25),outline=(25,20,15),width=2)
    d.text((lx+9,ly-5),name,fill=(246,230,24),stroke_width=2,stroke_fill=(35,24,20))
diagnostic.convert('RGB').save(OUT/'strasbourg-cities-vs-rhine.jpg',quality=95)
# QA at declared city center, and closed-out status.
report=dict(version='v016',status='GEOGRAPHIC QA ONLY; NOT APPROVED',
  painting_source='assets/reference/rhine-v011-full-painted-strip-overlay-3600x4800.png',
  reference='maps/canvas/rhine-v012-geographic-overlay.png',
  reference_limit='Natural Earth 10m generalized modern centerline is not a historical 1618 channel map',
  water_color_detection='Threshold on RGBA painted blue water-like pixels; dark/noisy image can yield false positive/negative',
  geographic_rhine_visualized='Magenta centerline water and outline superimposed over ORIGINAL painting in QA only',
  cities=sites,bands=rows,rows=sample,
  historical_concerns=[
   'Strasbourg is on the Ill west of main Rhine; do not imply main Rhine physically encircles cathedral',
   'Wide braided channel, islands and meanders depicted by painting cannot be accepted without period evidence',
   'Modern coarse Rhine centerline alone cannot verify 1618 Rhine channel braiding and banks',
   'City-painted river paths must align correctly at Mainz, Worms, Speyer, Strasbourg and Basel',
   'Verify historic city architecture and city-scale relative distances'
  ],
  print_approved=False,
  source_painting_modified=False,
  disposition='HOLD geography/river placement pending section-by-section correction if measured drift is material')
(OUT/'qa.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'status':report['status'],'bands':rows},indent=2))
