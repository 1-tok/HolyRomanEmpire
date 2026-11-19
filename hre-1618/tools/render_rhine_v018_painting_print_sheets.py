#!/usr/bin/env python3
"""Rebuild v018 printed painting sheets and candidate canvas from registered source.

Source is the genuine candidate PNG; no procedural city substitutions.
Requires a losslessly transferred binary at assets/reference/rhine-v018-city-bearing-painting.png.
Every sheet uses the same global pixel grid, so join identity is guaranteed.
Not a historical/300-PPI print approval.
"""
from pathlib import Path
import json,hashlib
import numpy as np, cv2
from PIL import Image,ImageFilter,ImageDraw
from scipy.interpolate import RBFInterpolator
R=Path(__file__).resolve().parents[1]
SRC=R/'assets/reference/rhine-v018-city-bearing-painting.png'
OUT=R/'reports/rhine-v018-geographic-print-sheets'
CAN=R/'maps/canvas'
for f in [OUT,CAN]:f.mkdir(exist_ok=True,parents=True)
if not SRC.is_file():raise SystemExit('Missing v018 original painted PNG. No substitute artwork allowed.')
source=Image.open(SRC).convert('RGBA')
assert source.size==(1024,1536)
src={
'Koblenz':(168,132),'Boppard':(131,231),'Bingen':(220,365),
'Mainz':(345,454),'Frankfurt':(689,366),'Hanau':(958,354),
'Aschaffenburg':(952,555),'Oppenheim':(224,612),
'Worms':(465,646),'Speyer':(479,800),'Germersheim':(592,879),
'Strasbourg':(245,951),'Breisach':(310,1125),'Neuenburg':(310,1266),'Basel':(357,1450)}
target={
'Koblenz':(1019.2,1855.51),'Boppard':(1016,1905.3),'Bingen':(1090.94,2013.32),
'Mainz':(1185.33,2003.05),'Frankfurt':(1292.61,1962.31),'Hanau':(1352.63,1954.97),
'Aschaffenburg':(1410.58,2019.16),'Oppenheim':(1205.83,2062.78),
'Worms':(1205.24,2150.29),'Speyer':(1219.98,2275.12),'Germersheim':(1201.34,2312.05),
'Strasbourg':(1032.24,2563.43),'Breisach':(978.81,2775.59),
'Neuenburg':(969.68,2862.08),'Basel':(972.7,2963.71)}
locked=['Koblenz','Bingen','Mainz','Frankfurt','Hanau','Worms','Speyer','Strasbourg','Breisach','Basel']
s=np.array([src[x] for x in locked],float)
t=np.array([target[x] for x in locked],float)
edge=np.array([[0,0],[1024,0],[0,1536],[1024,1536],[512,0],[512,1536],
[0,512],[0,1024],[1024,512],[1024,1024]],float)
end=np.column_stack((800+.75*edge[:,0],1690+.87*edge[:,1]))
inverse=RBFInterpolator(np.vstack((t,end)),np.vstack((s,edge)),smoothing=100,kernel='thin_plate_spline')
X0,Y0,X1,Y1=740,1640,1640,3140
H,W=Y1-Y0,X1-X0
orig=np.asarray(source)
warped=np.zeros((H,W,4),np.uint8)
for y in range(0,H,100):
 h=min(100,H-y)
 yy,xx=np.mgrid[Y0+y:Y0+y+h,X0:X1]
 loc=inverse(np.stack([xx.ravel(),yy.ravel()],1)).reshape(h,W,2).astype('float32')
 warped[y:y+h]=cv2.remap(orig,loc[:,:,0],loc[:,:,1],interpolation=cv2.INTER_CUBIC,
  borderMode=cv2.BORDER_CONSTANT,borderValue=(0,0,0,0))
warped[:,:,3]=np.array(Image.fromarray(warped[:,:,3],'L').filter(ImageFilter.GaussianBlur(4)))
canvas=Image.new('RGBA',(3600,4800))
overlay=Image.fromarray(warped,'RGBA')
canvas.alpha_composite(overlay,(X0,Y0))
canvas.save(CAN/'rhine-v018-registered-artwork-review-overlay.png',optimize=True)
# Use real map underlay for preview; do not change approved v016 master.
base=Image.open(R/'base/base_3600.jpg').convert('RGBA')
preview=Image.alpha_composite(base,canvas)
preview.convert('RGB').save(CAN/'rhine-v018-candidate-on-real-map.jpg',quality=94)
full=overlay.resize((W*3,H*3),Image.Resampling.LANCZOS)
div=[0,1125,2250,3375,4500]
rebuilt=Image.new('RGBA',full.size)
parts=[]
for i in range(4):
 a,b=div[i:i+2]
 lo=max(0,a-120);hi=min(4500,b+120)
 sheet=full.crop((0,lo,W*3,hi))
 fn='rhine-v018-sheet-%02d.png'%(i+1)
 sheet.save(OUT/fn,optimize=True)
 part=sheet.crop((0,a-lo,W*3,b-lo))
 rebuilt.paste(part,(0,a))
 assert np.array_equal(np.asarray(sheet),np.asarray(full.crop((0,lo,W*3,hi))))
 parts.append({'name':fn,'final_map_global_placement_px':[X0*3,Y0*3+lo],
 'core_y_px':[a,b],'overlap_px':120,'sha256':hashlib.sha256((OUT/fn).read_bytes()).hexdigest()})
assert np.array_equal(np.asarray(full),np.asarray(rebuilt))
city_qa=[{'name':name,'target_map_px':target[name],'source_center_px':src[name],
          'source_residual_px':round(float(np.linalg.norm(inverse(np.array([target[name]]))[0]-np.array(src[name]))),2),
          'locked':name in locked} for name in src]
q={'status':'GEOREGISTRATION REVIEW: FULL PRINT AND HISTORIC ACCURACY NOT APPROVED',
   'source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),
   'source_native_px':list(source.size),'print_master_px':[10800,14400],
   'source_interpolated':True,'print_ready':False,'city_anchors':city_qa,
   'exact_pixel_seams':True,'sheet_count':4,'sheets':parts,
   'original_v016_unchanged':True,
   'geographic_historical_riverbank_qa':'PENDING; generalized point fit only'}
(OUT/'qa.json').write_text(json.dumps(q,indent=2)+'\n')
assert (CAN/'rhine-v018-candidate-on-real-map.jpg').exists()
print('PASS: 4 exact overlap sheets + geographically registered candidate on HRE base. PRINT APPROVAL FALSE.')
