#!/usr/bin/env python3
"""Measure a river's course through each of its sprite sites, in sheet (north-up) directions.

Usage: python3 -I tools/river_course.py <River> <rivers.zip> [name,name,...]   (prints JSON)
Reads river-sites.csv, finds the Natural Earth centreline vertices within 14 km of each site,
fits their direction, signs it by the order of sites along the river, and prints entry and exit
edges of a square canvas centred on the site, the flow direction, and the bank the site is on.
"""
import csv, math, os, struct, sys, zipfile
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
river,zpath=sys.argv[1],sys.argv[2]; names=set(sys.argv[3].split(",")) if len(sys.argv)>3 else {river}
a=6378137.0; f=1/298.257223563; e2=2*f-f*f; e=math.sqrt(e2); R=math.radians
def m_(p): return math.cos(p)/math.sqrt(1-e2*math.sin(p)**2)
def t_(p): return math.tan(math.pi/4-p/2)/((1-e*math.sin(p))/(1+e*math.sin(p)))**(e/2)
l1,l2,l0,lo0=44.84,53.02,48.93,10.67
n=(math.log(m_(R(l1)))-math.log(m_(R(l2))))/(math.log(t_(R(l1)))-math.log(t_(R(l2)))); F=m_(R(l1))/(n*t_(R(l1))**n); rho0=a*F*t_(R(l0))**n
def xy(la,lo):  # metres east, metres north in the sheet projection
    rho=a*F*t_(R(la))**n; th=n*(R(lo)-R(lo0)); return rho*math.sin(th), rho0-rho*math.cos(th)
z=zipfile.ZipFile(zpath); shp=z.read([q for q in z.namelist() if q.endswith(".shp")][0]); dbf=z.read([q for q in z.namelist() if q.endswith(".dbf")][0])
nrec,hl,rl=struct.unpack("<IHH",dbf[4:12]); flds=[]; p=32
while dbf[p]!=0x0D: flds.append((dbf[p:p+11].split(b"\0")[0].decode(),dbf[p+16])); p+=32
def rname(i):
    r=dbf[hl+i*rl:hl+(i+1)*rl]; o=1
    for nm,ln in flds:
        if nm=="name": return r[o:o+ln].decode("latin-1").strip("\x00 ")
        o+=ln
pts=[]; pos=100; k=0
while pos+8<=len(shp):
    cl=struct.unpack(">i",shp[pos+4:pos+8])[0]*2; rec=shp[pos+8:pos+8+cl]; pos+=8+cl
    if struct.unpack("<i",rec[:4])[0]==3 and rname(k) in names:
        np_,npt=struct.unpack("<ii",rec[36:44]); q=struct.unpack("<%dd"%(2*npt),rec[44+4*np_:44+4*np_+16*npt])
        pts+= [xy(q[2*i+1],q[2*i]) for i in range(npt)]
    k+=1
sites=[r for r in csv.DictReader(open(os.path.join(ROOT,"river-sites.csv"),encoding="utf-8")) if r["river"]==river]
sites.sort(key=lambda r:int(r["order"])); P=[xy(float(r["lat"]),float(r["lon"])) for r in sites]
import json
compass=["north","north-east","east","south-east","south","south-west","west","north-west"]
FLOW={"north":("bottom","top"),"north-east":("bottom-left","top-right"),"east":("left","right"),"south-east":("top-left","bottom-right"),
      "south":("top","bottom"),"south-west":("top-right","bottom-left"),"west":("right","left"),"north-west":("bottom-right","top-left")}
def cdir(dx,dy): return compass[int(round((math.degrees(math.atan2(dx,dy))%360)/45))%8]
# sites on separate branches, where the next-site direction is meaningless: flow direction and river side set by hand
OVERRIDE={"Arnhem":("west","south"),"Nijmegen":("west","north"),"Utrecht":("west",None)}
out=[]
for i,(r,(sx,sy)) in enumerate(zip(sites,P)):
    near=[q for q in pts if math.hypot(q[0]-sx,q[1]-sy)<14000]
    if len(near)<4 and r["site"] not in OVERRIDE: out.append({"site":r["site"],"error":"no river vertices nearby"}); continue
    flow=side=None; dist=None
    if len(near)>=4:
        mx=sum(q[0] for q in near)/len(near); my=sum(q[1] for q in near)/len(near)
        sxx=sum((q[0]-mx)**2 for q in near); syy=sum((q[1]-my)**2 for q in near); sxy=sum((q[0]-mx)*(q[1]-my) for q in near)
        th=0.5*math.atan2(2*sxy,sxx-syy); ux,uy=math.cos(th),math.sin(th)
        fx,fy=(P[i+1][0]-sx,P[i+1][1]-sy) if i+1<len(P) else (sx-P[i-1][0],sy-P[i-1][1])
        if ux*fx+uy*fy<0: ux,uy=-ux,-uy
        nb=min(near,key=lambda q:math.hypot(q[0]-sx,q[1]-sy)); vx,vy=nb[0]-sx,nb[1]-sy; dot=vx*ux+vy*uy
        px_,py_=vx-dot*ux,vy-dot*uy; dist=math.hypot(px_,py_); flow=cdir(ux,uy); side=cdir(px_,py_) if dist>=400 else None
    if r["site"] in OVERRIDE: flow,side=OVERRIDE[r["site"]]
    ent,ext=FLOW[flow]
    out.append({"order":int(r["order"]),"site":r["site"],"flow":flow,"enters":ent,"leaves":ext,"river_side":side,"river_km":None if dist is None else round(dist/1000,1)})
print(json.dumps(out,ensure_ascii=False))
