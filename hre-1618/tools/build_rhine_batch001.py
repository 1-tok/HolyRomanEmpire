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
        if i<len(names) and names[i] in ('rhine','rhein','rhin','waal','nederrijn','neder rijn','lek','ijssel','oude rijn') and struct.unpack('<i',rec[:4])[0]==3:
            np,nt=struct.unpack('<ii',rec[36:44])
            ix=list(struct.unpack('<%di'%np,rec[44:44+4*np]))+[nt]
            raw=struct.unpack('<%dd'%(2*nt),rec[44+4*np:44+4*np+16*nt])
            for j in range(np):
                points=[(raw[2*k+1],raw[2*k]) for k in range(ix[j],ix[j+1])]
                if len(points)>1 and any(47.3<lat<52.4 and 4.7<lon<9.1 for lat,lon in points):
                    lines.append(points)
        i+=1
    if not lines: raise ValueError('No Rhine/Waal/Nederrijn features found in the 10m source')
    return lines

def overlay(lines):
    im=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(im);segments=0
    for line in lines:
        for (a,b),(c,e) in zip(line,line[1:]):
            if min(a,c)>52.4 or max(a,c)<47.35:continue
            if min(b,e)>9.1 or max(b,e)<4.7:continue
            p=px(a,b);q=px(c,e)
            # Same geographic polyline as base; warmer hand-paint-like river fill
            d.line([p,q],fill=(63,111,143,220),width=15)
            d.line([p,q],fill=(81,143,168,200),width=9)
            d.line([p,q],fill=(154,189,187,100),width=2)
            segments+=1
    if segments<10:raise ValueError('River extraction incomplete')
    return im

def exact_connector_tiles(water):
    """Cut a single global water raster into pixel-exact transparent tiles.

    Each tile has a non-overlapping half-open Y range [y0, y1).
    No independent strokes or edge resampling; stitch uses copy, not blending.
    All coordinates refer to the unchanged 3600x4800 geographic canvas.
    """
    from hashlib import sha256
    DEST=ROOT/'assets'/'sprites'/'rivers'/'rhine'
    DEST.mkdir(parents=True,exist_ok=True)
    manifest=[]
    reconstructed=Image.new('RGBA',(W,H),(0,0,0,0))
    for i,y0 in enumerate(range(0,H,240),1):
        y1=min(H,y0+240)
        full_strip=water.crop((0,y0,W,y1))
        box=full_strip.getbbox()
        if box is None:
            continue
        crop=full_strip.crop(box)
        name=f'rhine-connector-{i:02d}.png'
        destination=DEST/name
        crop.save(destination,format='PNG',optimize=True)
        # Verify exactly the same bytes after file decode, no edge fading.
        tile=Image.open(destination).convert('RGBA')
        assert ImageChops.difference(tile,crop).getbbox() is None, name
        x,y=box[0],box[1]+y0
        reconstructed.paste(tile,(x,y))
        manifest.append({'file':name,'x':x,'y':y,'width':crop.width,
                         'height':crop.height,'range_y':[y0,y1],
                         'sha256':sha256(destination.read_bytes()).hexdigest()})
    mismatch=ImageChops.difference(reconstructed,water)
    # Image.getbbox() can mask RGB differences if alpha diff=0. Compare bands.
    assert not any(b.getbbox() for b in mismatch.split()), 'Connector seam/reassembly mismatch'
    (DEST/'manifest.json').write_text(json.dumps({
        'source_canvas':'base/base_3600.jpg',
        'water_geometry':'Natural Earth 10m river centerlines, same as tools/build_base.py',
        'global_coordinates':'north-up Lambert Conformal Conic, 3600x4800',
        'render_order':['existing base','river connectors','city sprites','labels'],
        'seam_qa':'PASS: reconstructed RGBA exactly equals canonical water raster',
        'tile_count':len(manifest),'connectors':manifest
    },indent=2)+'\n')
    return reconstructed,manifest

def render():
    config=json.loads(CFG.read_text())
    base=Image.open(ROOT/'base'/'base_3600.jpg').convert('RGBA')
    if base.size!=(W,H):
        raise ValueError('Original base map dimensions changed')
    data=Path(sys.argv[1]).read_bytes() if len(sys.argv)>1 else urllib.request.urlopen(SOURCE,timeout=90).read()
    water=overlay(river_lines(data))
    OUT.mkdir(parents=True,exist_ok=True)
    water.save(OUT/'continuous-rhine-water-overlay.png')
    rebuilt,connectors=exact_connector_tiles(water)
    # River water is assembled first; city painting goes ABOVE every tile.
    # No water mask is cut into a city's painted buildings or roofs.
    assembled=Image.alpha_composite(base,rebuilt)
    placements=[]
    for city in config['entries']:
        fn=ROOT/city['asset']
        if not fn.exists():
            print('Not yet committed:',fn)
            continue
        sprite=Image.open(fn).convert('RGBA')
        sz=config['working_sprite_width_px']
        sprite.thumbnail((sz,sz),Image.Resampling.LANCZOS)
        x=round(city['x'])-sprite.width//2
        y=round(city['y'])-sprite.height//2
        # NEVER erase sprite pixels to expose a river: the city is in front.
        assembled.alpha_composite(sprite,(x,y))
        placements.append({
            'site':city['site'],'file':city['asset'],
            'x':x,'y':y,'width':sprite.width,'height':sprite.height,
            'layer':'city-over-river', 'status':'provisional historical QA'
        })
    assembled.convert('RGB').save(OUT/'on-existing-base-3600.jpg',quality=93)
    # Per-city QA: compare the canonical river underlay against the opaque
    # and translucent city footprints. This identifies blocked watercourse
    # segments without drawing blue water ON TOP of buildings.
    qa_dir=OUT/'city-river-junctions'
    qa_dir.mkdir(parents=True,exist_ok=True)
    qa=[]
    for city in config['entries']:
        fn=ROOT/city['asset']
        if not fn.exists():
            continue
        sprite=Image.open(fn).convert('RGBA')
        sz=config['working_sprite_width_px']
        sprite.thumbnail((sz,sz),Image.Resampling.LANCZOS)
        x=round(city['x'])-sprite.width//2
        y=round(city['y'])-sprite.height//2
        region=(max(0,x-90),max(0,y-90),
                min(W,x+sprite.width+90),min(H,y+sprite.height+90))
        x0,y0,x1,y1=region
        local=water.crop(region)
        at=(x-x0,y-y0)
        overlay_alpha=Image.new('L',local.size,0)
        overlay_alpha.paste(sprite.getchannel('A'),at)
        opaque_mask=overlay_alpha.point(lambda a:255 if a>=224 else 0)
        water_mask=local.getchannel('A').point(lambda a:255 if a>0 else 0)
        blocked=ImageChops.multiply(water_mask,opaque_mask)
        opaque_water_px=sum(1 for v in blocked.getdata() if v)
        water_px=sum(1 for v in water_mask.getdata() if v)
        img=assembled.crop(region).convert('RGB')
        # Diagnostic only: colored outlines are drawn on separate QA views,
        # never into the actual composite.
        diagnostic=img.copy()
        dd=ImageDraw.Draw(diagnostic)
        dd.rectangle((x-x0,y-y0,x-x0+sprite.width-1,y-y0+sprite.height-1),
                     outline=(210,130,38),width=2)
        dd.text((8,8),city['site']+' | top-layer sprite',
                fill=(30,31,25),stroke_width=2,stroke_fill=(246,244,224))
        safe=''.join(c if c.isalnum() or c in '-_' else '-' for c in city['site'])
        diagnostic.resize((480,480),Image.Resampling.LANCZOS).save(qa_dir/(safe+'-junction.png'))
        # The paint occupies the true river corridor where blocked > 0.
        # That does NOT mean it is historically correct. Flag for bank QA.
        qa.append({'site':city['site'],'raster_crop_xyxy':list(region),
                   'river_pixels_within_qa_crop':water_px,
                   'canonical_water_pixels_behind_opaque_city':opaque_water_px,
                   'qa_image':'city-river-junctions/'+safe+'-junction.png',
                   'status':'NEEDS_VISUAL_QA'})
    (OUT/'city-river-junction-qa.json').write_text(json.dumps({
        'city_layer_is_above_river':True,
        'water_sprite_seam_qa':'exact pre-city raster; passed by exact_connector_tiles',
        'historical_river_alignment':'not verified',
        'note':'Water behind an opaque city is not visible; review coast and painted local water manually',
        'sites':qa
    },indent=2,ensure_ascii=False)+'\n')
    # Use the same connector raster for previews and downstream print builds.
    report={'city_placements':placements,'connector_sprites':connectors,
       'connector_directory':'assets/sprites/rivers/rhine',
       'render_order':['original base','connector sprites','city sprites','labels'],
       'seam_test':'PASS: exact RGBA reconstruction',
       'visual_qa':'City sprites preserve original opaque/alpha artwork; local painted water may need shoreline QA',
       'historical_status':'PROVISIONAL: NE 10m course is not a 1618 reconstruction'}
    (OUT/'placements.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Rhine connector tiles:',len(connectors),'exact seams; city sprites on top:',len(placements))

if __name__=='__main__':
    render()
