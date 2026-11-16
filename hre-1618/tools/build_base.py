#!/usr/bin/env python3
"""Build the HRE 1618 base map underlay (3600 x 4800 px, quarter of the 10800 x 14400 master).

Layers: height-tinted land with NW hillshade, sea shaded by distance from coast,
period water (Zuiderzee, hand-drawn approximation), lakes and rivers (Natural Earth 10m),
1618 territory borders (ETH Zurich, territories over 3000 km2), city dots and river sprite sites. No lettering.
Run:  python3 -I tools/build_base.py <work_dir>      (needs Pillow; downloads data into work_dir)
"""
import math, sys, os, io, struct, zipfile, urllib.request
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
WORK = sys.argv[1]; os.makedirs(WORK, exist_ok=True)
ETH = os.path.join(ROOT, "data", "eth-territories")
MIN_TERR = 3000   # km2: territories smaller than this are left out of the borders
MIN_RING = 600    # km2: fragments and enclaves smaller than this are not drawn
OUT = os.path.join(ROOT, "base")

a=6378137.0; f=1/298.257223563; e2=2*f-f*f; e=math.sqrt(e2); R=math.radians; DG=math.degrees
def m_(p): return math.cos(p)/math.sqrt(1-e2*math.sin(p)**2)
def t_(p): return math.tan(math.pi/4-p/2)/((1-e*math.sin(p))/(1+e*math.sin(p)))**(e/2)
lat1,lat2,lat0,lon0=44.84,53.02,48.93,10.67
XMIN,XMAX,YMIN,YMAX=-503671,504058,-661508,682131
n=(math.log(m_(R(lat1)))-math.log(m_(R(lat2))))/(math.log(t_(R(lat1)))-math.log(t_(R(lat2))))
F=m_(R(lat1))/(n*t_(R(lat1))**n); rho0=a*F*t_(R(lat0))**n
def fwd(la,lo):
    rho=a*F*t_(R(la))**n; th=n*(R(lo)-R(lon0)); return rho*math.sin(th), rho0-rho*math.cos(th)
def inv(x,y):
    dy=rho0-y; rho=math.hypot(x,dy); th=math.atan2(x,dy); tt=(rho/(a*F))**(1/n); phi=math.pi/2-2*math.atan(tt)
    for _ in range(6): phi=math.pi/2-2*math.atan(tt*((1-e*math.sin(phi))/(1+e*math.sin(phi)))**(e/2))
    return DG(phi), DG(R(lon0)+th/n)
W,H=3600,4800
def px(la,lo):
    x,y=fwd(la,lo); return ((x-XMIN)/(XMAX-XMIN)*W, (YMAX-y)/(YMAX-YMIN)*H)

def get(url,name):
    p=os.path.join(WORK,name)
    if not os.path.exists(p):
        urllib.request.urlretrieve(url,p)
    return p
def read_shp(zpath):
    z=zipfile.ZipFile(zpath); shp=z.read([q for q in z.namelist() if q.endswith('.shp')][0])
    dbf=[q for q in z.namelist() if q.endswith('.dbf')]; names=None
    if dbf: names=read_dbf(z.read(dbf[0]))
    out=[]; pos=100; k=0
    while pos+8<=len(shp):
        cl=struct.unpack('>i',shp[pos+4:pos+8])[0]*2; rec=shp[pos+8:pos+8+cl]; pos+=8+cl
        st=struct.unpack('<i',rec[:4])[0]
        if st in (3,5):
            bb=struct.unpack('<4d',rec[4:36]); np_,npt=struct.unpack('<ii',rec[36:44])
            parts=list(struct.unpack('<%di'%np_,rec[44:44+4*np_]))+[npt]
            pts=struct.unpack('<%dd'%(2*npt),rec[44+4*np_:44+4*np_+16*npt]); P=[(pts[2*i+1],pts[2*i]) for i in range(npt)]
            out.append((bb,[P[parts[j]:parts[j+1]] for j in range(np_)],names[k] if names else None))
        k+=1
    return out
def read_dbf(b):
    n_=struct.unpack('<I',b[4:8])[0]; hl,rl=struct.unpack('<HH',b[8:12]); fields=[];p=32
    while b[p]!=0x0D: fields.append((b[p:p+11].split(b'\0')[0].decode(),b[p+16])); p+=32
    rows=[]
    for i in range(n_):
        r=b[hl+i*rl:hl+(i+1)*rl]; o=1; d={}
        for nm,ln in fields: d[nm]=r[o:o+ln].decode('latin-1').strip(); o+=ln
        rows.append(d)
    return rows
def bb_hit(bb):  # bb = xmin,ymin,xmax,ymax in lon/lat; frame covers lon ~-1..24, lat ~41..58
    return not (bb[2]<-3 or bb[0]>26 or bb[3]<40 or bb[1]>60)
def clip(poly,x0,y0,x1,y1):
    def side(P,inside,inter):
        out=[]
        for i in range(len(P)):
            c,p=P[i],P[i-1]
            if inside(c):
                if not inside(p): out.append(inter(p,c))
                out.append(c)
            elif inside(p): out.append(inter(p,c))
        return out
    def ix(xv):
        return lambda p,c:(xv,p[1]+(c[1]-p[1])*(xv-p[0])/(c[0]-p[0]))
    def iy(yv):
        return lambda p,c:(p[0]+(c[0]-p[0])*(yv-p[1])/(c[1]-p[1]),yv)
    P=poly
    for ins,it in ((lambda q:q[0]>=x0,ix(x0)),(lambda q:q[0]<=x1,ix(x1)),(lambda q:q[1]>=y0,iy(y0)),(lambda q:q[1]<=y1,iy(y1))):
        if not P: return []
        P=side(P,ins,it)
    return P
def ring_px(ring): return [px(la,lo) for la,lo in ring]

print("data..."); sys.stdout.flush()
land=read_shp(get("https://naturalearth.s3.amazonaws.com/10m_physical/ne_10m_land.zip","land.zip"))
lakes=read_shp(get("https://naturalearth.s3.amazonaws.com/10m_physical/ne_10m_lakes.zip","lakes.zip"))
rivers=read_shp(get("https://naturalearth.s3.amazonaws.com/10m_physical/ne_10m_rivers_lake_centerlines.zip","rivers.zip"))

# --- land mask (full res)
mask=Image.new('L',(W,H),0); md=ImageDraw.Draw(mask)
for bb,rings,_ in land:
    if not bb_hit(bb): continue
    for r in rings:
        P=clip(ring_px(r),-200,-200,W+200,H+200)
        if len(P)>2: md.polygon(P,fill=255)
for bb,rings,_ in lakes:
    if not bb_hit(bb): continue
    for r in rings:
        P=clip(ring_px(r),-200,-200,W+200,H+200)
        if len(P)>2: md.polygon(P,fill=0)
# period water: Zuiderzee (approximate hand-drawn outline, see spec)
zz=[(52.78,5.10),(52.70,5.28),(52.64,5.06),(52.51,5.05),(52.33,5.07),(52.30,5.16),(52.25,5.37),(52.34,5.62),(52.45,5.84),(52.56,5.91),(52.62,5.98),(52.73,5.97),(52.84,5.71),(52.88,5.36),(53.00,5.30),(53.05,5.15),(52.98,5.02)]
md.polygon([px(*p) for p in zz],fill=0)
print("mask done"); sys.stdout.flush()

# --- terrain (AWS terrarium z7) on a coarse grid
Z=7; N=2**Z; GW,GH=720,960
cellx=(XMAX-XMIN)/GW; celly=(YMAX-YMIN)/GH
def tilexy(la,lo):
    return (lo+180)/360*N,(1-math.log(math.tan(R(la))+1/math.cos(R(la)))/math.pi)/2*N
cs=[inv(XMIN,YMIN),inv(XMAX,YMIN),inv(XMIN,YMAX),inv(XMAX,YMAX)]
tx=[tilexy(*c)[0] for c in cs]; ty=[tilexy(*c)[1] for c in cs]; tiles={}
for ix in range(int(min(tx)),int(max(tx))+1):
    for iy in range(int(min(ty)),int(max(ty))+1):
        p=get(f"https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{Z}/{ix}/{iy}.png",f"t_{ix}_{iy}.png")
        tiles[(ix,iy)]=Image.open(p).convert('RGB').load()
Hh=[[0.0]*GW for _ in range(GH)]
for j in range(GH):
    y=YMAX-(j+0.5)*celly
    for i in range(GW):
        la,lo=inv(XMIN+(i+0.5)*cellx,y); gx,gy=tilexy(la,lo); k=(int(gx),int(gy))
        if k in tiles:
            r,g,b=tiles[k][min(int((gx-k[0])*256),255),min(int((gy-k[1])*256),255)]
            Hh[j][i]=max(r*256+g+b/256-32768,0.0)
print("dem done"); sys.stdout.flush()
pal=[(0,(167,189,134)),(120,(184,196,140)),(300,(196,180,134)),(550,(172,152,122)),(900,(156,150,142)),(1500,(168,164,158)),(2300,(240,238,232))]
def tint(h):
    for (h0,c0),(h1,c1) in zip(pal,pal[1:]):
        if h<=h1:
            k=max(0,(h-h0)/(h1-h0)); return tuple(int(c0[q]+(c1[q]-c0[q])*k) for q in range(3))
    return pal[-1][1]
g=Image.new('RGB',(GW,GH)); gp=g.load()
for j in range(GH):
    for i in range(GW):
        h=Hh[j][i]; base=tint(h)
        dx=(Hh[j][min(i+1,GW-1)]-Hh[j][max(i-1,0)])/(2*cellx); dy=(Hh[min(j+1,GH-1)][i]-Hh[max(j-1,0)][i])/(2*celly)
        s=math.atan(math.hypot(dx,dy)); asp=math.atan2(-dx,dy)
        sh=math.cos(R(45))*math.cos(s)+math.sin(R(45))*math.sin(s)*math.cos(R(315)-asp)
        k=0.82+0.55*(sh-0.7)
        gp[i,j]=tuple(max(0,min(255,int(c*k))) for c in base)
landimg=g.resize((W,H),Image.BICUBIC)

# --- sea: lighter near coast, darker offshore
small=mask.resize((W//4,H//4),Image.BILINEAR).filter(ImageFilter.GaussianBlur(28)).resize((W,H),Image.BILINEAR)
shallow=(127,163,180); deep=(70,112,139)
lut=[tuple(int(deep[c]+(shallow[c]-deep[c])*min(1,v/255*2.4)) for c in range(3)) for v in range(256)]
sea=Image.merge('RGB',[small.point([l[c] for l in lut]) for c in range(3)])
img=Image.composite(landimg,sea,mask)
d=ImageDraw.Draw(img)

# --- borders from ETH territories (>1500 km2, active in 1618), clipped to land
def dbf_rows(path):
    return read_dbf(open(path,'rb').read())
rows=dbf_rows(os.path.join(ETH,"territories_manual.dbf")); shp=open(os.path.join(ETH,"territories_manual.shp"),'rb').read()
polys=[]; pos=100
while pos+8<=len(shp):
    cl=struct.unpack('>i',shp[pos+4:pos+8])[0]*2; rec=shp[pos+8:pos+8+cl]; pos+=8+cl
    if struct.unpack('<i',rec[:4])[0]!=5: polys.append(None); continue
    np_,npt=struct.unpack('<ii',rec[36:44]); parts=list(struct.unpack('<%di'%np_,rec[44:44+4*np_]))+[npt]
    pts=struct.unpack('<%dd'%(2*npt),rec[44+4*np_:44+4*np_+16*npt]); P=[(pts[2*i+1],pts[2*i]) for i in range(npt)]
    polys.append([P[parts[j]:parts[j+1]] for j in range(np_)])
def yr(s):
    try: return float(s)
    except: return None
def km2(rings):
    tot=0
    for r in rings:
        s=0
        for (y1,x1),(y2,x2) in zip(r,r[1:]+r[:1]):
            s+=(x1*math.cos(math.radians(y1))*111.32)*(y2*110.57)-(x2*math.cos(math.radians(y2))*111.32)*(y1*110.57)
        tot+=s/2
    return abs(tot)
seen=set(); blayer=Image.new('L',(W,H),0); bd=ImageDraw.Draw(blayer); nb=0; used=[]
for i,r in enumerate(rows):
    y0,y1=yr(r['start']),yr(r['end'])
    if not((y0 is None or y0<=1618) and (y1 is None or y1>1618)) or polys[i] is None: continue
    if r['idx_poly'] in seen: continue
    seen.add(r['idx_poly'])
    if km2(polys[i])<MIN_TERR: continue
    nb+=1; used.append(r['name'])
    for ring in polys[i]:
        if len(ring)<3 or any(not(30<la<65 and -10<lo<35) for la,lo in ring) or km2([ring])<MIN_RING: continue
        pts=ring_px(ring); bd.line(pts+[pts[0]],fill=255,width=4,joint='curve')
blayer=Image.composite(blayer,Image.new('L',(W,H),0),mask)
img.paste(Image.new('RGB',(W,H),(112,46,36)),(0,0),blayer.point(lambda v:int(v*0.85)))
print("borders",nb); sys.stdout.flush()

# --- coast line, lakes, rivers
for bb,rings,_ in land:
    if not bb_hit(bb): continue
    for r in rings:
        P=ring_px(r); P=[q for q in P if -300<q[0]<W+300 and -300<q[1]<H+300]
        for k in range(len(P)-1):
            if math.hypot(P[k+1][0]-P[k][0],P[k+1][1]-P[k][1])<60: d.line([P[k],P[k+1]],fill=(86,66,44),width=3)
big={'Rhine','Rhein','Danube','Donau','Elbe','Oder','Vistula','Weser','Po'}
for bb,lines,nm in rivers:
    if not bb_hit(bb): continue
    name=(nm or {}).get('name','')
    w=7 if name in big else 4
    for ln in lines:
        P=ring_px(ln)
        for k in range(len(P)-1):
            x0,y0=P[k]; x1,y1=P[k+1]
            if (-50<x0<W+50 and -50<y0<H+50) or (-50<x1<W+50 and -50<y1<H+50):
                d.line([P[k],P[k+1]],fill=(63,111,143),width=w)
# --- city dots
cities=[("Amsterdam",52.37,4.90,1),("Utrecht",52.09,5.12,1),("Brussels",50.85,4.35,1),("Antwerp",51.22,4.40,1),("Ghent",51.05,3.72,1),("Liege",50.63,5.57,1),("Luxembourg",49.61,6.13,1),("Cologne",50.94,6.96,1),("Frankfurt",50.11,8.68,1),("Heidelberg",49.41,8.71,1),("Metz",49.12,6.18,1),("Strasbourg",48.58,7.75,1),("Stuttgart",48.78,9.18,1),("Ulm",48.40,9.99,1),("Augsburg",48.37,10.90,1),("Munich",48.14,11.58,1),("Nuremberg",49.45,11.08,1),("Regensburg",49.01,12.10,1),("Linz",48.31,14.29,1),("Vienna",48.21,16.37,1),("Graz",47.07,15.44,1),("Salzburg",47.80,13.04,1),("Innsbruck",47.27,11.39,1),("Prague",50.09,14.42,1),("Dresden",51.05,13.74,1),("Leipzig",51.34,12.37,1),("Berlin",52.52,13.40,1),("Magdeburg",52.13,11.64,1),("Hamburg",53.55,9.99,1),("Lubeck",53.87,10.69,1),("Bremen",53.08,8.80,1),("Hanover",52.37,9.73,1),("Kassel",51.31,9.50,1),("Breslau",51.11,17.03,1),("Stralsund",54.31,13.09,1),("Kiel",54.32,10.14,1),("Milan",45.46,9.19,1),("Mantua",45.16,10.79,1),("Trento",46.07,11.12,1),("Lille",50.63,3.06,0),("Paris",48.86,2.35,0),("Lyon",45.76,4.84,0),("Geneva",46.20,6.14,0),("Bern",46.95,7.45,0),("Zurich",47.37,8.54,0),("Basel",47.56,7.59,0),("Turin",45.07,7.69,0),("Genoa",44.41,8.93,0),("Florence",43.77,11.25,0),("Bologna",44.49,11.34,0),("Trieste",45.65,13.78,0),("Ljubljana",46.06,14.51,0),("Zagreb",45.81,15.98,0),("Posen",52.41,16.93,0),("Schleswig",54.52,9.56,0)]
for nm,la,lo,inh in cities:
    x,y=px(la,lo)
    if 0<x<W and 0<y<H:
        d.ellipse((x-15,y-15,x+15,y+15),fill=(150,30,25) if inh else (70,70,82),outline=(40,20,10),width=2)
# river sprite sites (river-sites.csv): cream dot with ink ring, drawn over the plain city dots
import csv
for row in csv.DictReader(open(os.path.join(ROOT,"river-sites.csv"),encoding="utf-8")):
    if not row["on_sheet"].startswith("yes"): continue
    x,y=px(float(row["lat"]),float(row["lon"]))
    d.ellipse((x-15,y-15,x+15,y+15),fill=(244,234,205),outline=(40,20,10),width=4)
d.rectangle((0,0,W-1,H-1),outline=(90,70,40),width=14)
os.makedirs(OUT,exist_ok=True)
img.save(os.path.join(OUT,"base_3600.jpg"),quality=88)
img.resize((1200,1600),Image.LANCZOS).save(os.path.join(OUT,"base_preview_1200.jpg"),quality=88)
open(os.path.join(OUT,"borders_used.txt"),'w').write("\n".join(sorted(set(used))))
print("DONE"); 
