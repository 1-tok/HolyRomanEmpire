#!/usr/bin/env python3
"""Place Rhine Batch 001 city artwork on the existing HRE 1618 geographic base.

NE 10m water geometry uses the same source/projection as tools/build_base.py.
This is a provisional geographic/rendering QA pass, not a verified AD 1618
historical river reconstruction. Run from hre-1618/:
  python3 tools/build_rhine_batch001.py [path/to/rivers.zip]
"""
import io, json, math, struct, sys, urllib.request, zipfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageChops, ImageFilter

ROOT=Path(__file__).resolve().parents[1]
CFG=ROOT/'placements/rhine-batch-001.json'
OUT=ROOT/'reports/rhine-batch-001'
SOURCE='https://naturalearth.s3.amazonaws.com/10m_physical/ne_10m_rivers_lake_centerlines.zip'
W,H=3600,4800
rad=math.radians; a=6378137.; f=1/298.257223563; ecc=math.sqrt(2*f-f*f)
def m(p): return math.cos(p)/math.sqrt(1-(ecc*math.sin(p))**2)
def t(p): return math.tan(math.pi/4-p/2)/((1-ecc*math.sin(p))/(1+ecc*math.sin(p)))**(ecc/2)
lat1,lat2,lat0,lon0=44.84,53.02,48.93,10.67
n=math.log(m(rad(lat1))/m(rad(lat2)))/math.log(t(rad(lat1))/t(rad(lat2)))
F=m(rad(lat1))/(n*t(rad(lat1))**n); rho0=a*F*t(rad(lat0))**n
def px(lat,lon):
    rho=a*F*t(rad(lat))**n; theta=n*rad(lon-lon0)
    x=rho*math.sin(theta); y=rho0-rho*math.cos(theta)
    return ((x+503671)/1007729*W,(682131-y)/1343639*H)

def river_lines(payload):
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        shp=z.read(next(s for s in z.namelist() if s.endswith('.shp')))
        dbf=z.read(next(s for s in z.namelist() if s.endswith('.dbf')))
    count=struct.unpack('<I',dbf[4:8])[0]; head,step=struct.unpack('<HH',dbf[8:12])
    fields=[]; q=32
    while dbf[q]!=13:
        fields.append((dbf[q:q+11].split(b'\0')[0].decode(),dbf[q+16]));q+=32
    names=[]
    for i in range(count):
        rr=dbf[head+i*step:head+(i+1)*step]; pos=1; name=''
        for key,size in fields:
            if key=='name':name=rr[pos:pos+size].decode('latin1').strip('\0 ')
            pos+=size
        names.append(name.lower())
    pos=100; i=0; lines=[]
    while pos+8<=len(shp):
        length=struct.unpack('>i',shp[pos+4:pos+8])[0]*2
        rec=shp[pos+8:pos+8+length];pos+=8+length
        if i<len(names) and names[i] in ('rhine','rhein','rhin') and struct.unpack('<i',rec[:4])[0]==3:
            np,nt=struct.unpack('<ii',rec[36:44])
            ix=list(struct.unpack('<%di'%np,rec[44:44+4*np]))+[nt]
            raw=struct.unpack('<%dd'%(2*nt),rec[44+4*np:44+4*np+16*nt])
            for j in range(np):
                points=[(raw[2*k+1],raw[2*k]) for k in range(ix[j],ix[j+1])]
                if len(points)>1 and any(47.4<lat<50.15 and 7.15<lon<8.95 for lat,lon in points):
                    lines.append(points)
        i+=1
    if not lines: raise ValueError('No Rhine/Rhein/Rhin features found in the 10m source')
    return lines

def overlay(lines):
    im=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(im);segments=0
    for line in lines:
        for (a,b),(c,e) in zip(line,line[1:]):
            if min(a,c)>50.12 or max(a,c)<47.45:continue
            if min(b,e)>8.95 or max(b,e)<7.15:continue
            p=px(a,b);q=px(c,e)
            # Same geographic polyline as base; warmer hand-paint-like river fill
            d.line([p,q],fill=(63,111,143,220),width=15)
            d.line([p,q],fill=(81,143,168,200),width=9)
            d.line([p,q],fill=(154,189,187,100),width=2)
            segments+=1
    if segments<10:raise ValueError('River extraction incomplete')
    return im

def render():
    config=json.loads(CFG.read_text())
    path=ROOT/'base/base_3600.jpg'
    base=Image.open(path).convert('RGBA')
    if base.size!=(W,H):raise ValueError('Base map geometry must remain 3600x4800')
    if len(sys.argv)>1:data=Path(sys.argv[1]).read_bytes()
    else:data=urllib.request.urlopen(SOURCE,timeout=90).read()
    water=overlay(river_lines(data));OUT.mkdir(parents=True,exist_ok=True)
    water.save(OUT/'continuous-rhine-water-overlay.png')
    # The connector sprites are disjoint slices from the SAME water layer.
    # Their stored x,y placement reconstitutes a perfectly continuous river.
    cities=config['entries'];boundaries=[0]
    boundaries+=sorted(round((cities[i]['y']+cities[i+1]['y'])/2) for i in range(len(cities)-1))
    boundaries.append(H)
    connectors=[]
    for i,(y0,y1) in enumerate(zip(boundaries,boundaries[1:])):
        band=water.crop((0,y0,W,y1));bb=band.getbbox()
        if bb:
            file=f'connector-{i+1:02d}.png'
            crop=band.crop(bb);crop.save(OUT/file)
            connectors.append({'file':file,'x':bb[0],'y':y0+bb[1],'width':crop.width,'height':crop.height})
    # Protect the pre-existing water geometry wherever a city vignette has
    # its own painted water. Historic bridge overlays require later QA.
    protected=water.getchannel('A').point(lambda a:255 if a>0 else 0).filter(ImageFilter.MaxFilter(9))
    assembled=Image.alpha_composite(base,water);placements=[]
    for city in cities:
        fn=ROOT/city['asset']
        if not fn.exists():
            print('Missing (upload ZIP sprite first):',fn)
            continue
        sprite=Image.open(fn).convert('RGBA')
        sz=config['working_sprite_width_px'];sprite.thumbnail((sz,sz),Image.Resampling.LANCZOS)
        x=round(city['x'])-sprite.width//2;y=round(city['y'])-sprite.height//2
        sprite.putalpha(ImageChops.subtract(sprite.getchannel('A'),protected.crop((x,y,x+sprite.width,y+sprite.height))))
        assembled.alpha_composite(sprite,(x,y))
        placements.append({'site':city['site'],'file':city['asset'],'x':x,'y':y,'width':sprite.width,'height':sprite.height})
    assembled.convert('RGB').save(OUT/'on-existing-base-3600.jpg',quality=93)
    (OUT/'placements.json').write_text(json.dumps({'city_placements':placements,'connector_sprites':connectors,'status':'PROVISIONAL QA; modern generalized NE10m reference; bridges not yet verified'},indent=2)+'\n')
    print('Wrote',OUT, 'cities placed:',len(placements),'connectors:',len(connectors))

if __name__=='__main__':render()
