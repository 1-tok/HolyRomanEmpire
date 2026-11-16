#!/usr/bin/env python3
"""Look up coordinates for every city in river-manifest.md from Wikidata (P625).

For each place a search term and an expected position (my own estimate, used only to pick the
right Wikidata item and to flag disagreement) are given below. The chosen item is the search
result with coordinates nearest the estimate, within 25 km. Output: river-sites.csv.
Run: python3 -I tools/lookup_river_sites.py     (standard library only)
"""
import csv, json, math, os, re, time, urllib.error, urllib.parse, urllib.request
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
UA="HRE1618-map/1.0 (personal historical map project)"
# manifest place -> (search term, expected lat, expected lon)
P={
"Basel":("Basel",47.56,7.59),"Strasbourg":("Strasbourg",48.58,7.75),"Speyer":("Speyer",49.32,8.43),"Worms":("Worms",49.63,8.36),
"Mainz":("Mainz",50.00,8.27),"Koblenz":("Koblenz",50.36,7.59),"Bonn":("Bonn",50.73,7.10),"Cologne":("Cologne",50.94,6.96),
"Düsseldorf":("Düsseldorf",51.23,6.78),"Duisburg":("Duisburg",51.43,6.76),"Wesel":("Wesel",51.66,6.62),"Arnhem":("Arnhem",51.98,5.91),
"Nijmegen":("Nijmegen",51.84,5.86),"Utrecht":("Utrecht",52.09,5.12),"Ulm":("Ulm",48.40,9.99),"Donauwörth":("Donauwörth",48.72,10.78),
"Ingolstadt":("Ingolstadt",48.76,11.42),"Regensburg":("Regensburg",49.01,12.10),"Straubing":("Straubing",48.88,12.57),"Passau":("Passau",48.57,13.46),
"Linz":("Linz",48.31,14.29),"Vienna":("Vienna",48.21,16.37),"Pressburg (Bratislava)":("Bratislava",48.15,17.11),"Győr":("Győr",47.69,17.63),
"Dresden":("Dresden",51.05,13.74),"Meissen":("Meissen",51.16,13.47),"Torgau":("Torgau",51.56,13.00),"Wittenberg":("Wittenberg",51.87,12.65),
"Dessau":("Dessau",51.84,12.24),"Magdeburg":("Magdeburg",52.13,11.64),"Tangermünde":("Tangermünde",52.54,11.97),"Lauenburg":("Lauenburg/Elbe",53.37,10.55),
"Hamburg":("Hamburg",53.55,9.99),"Ratibor (Racibórz)":("Racibórz",50.09,18.22),"Oppeln (Opole)":("Opole",50.67,17.93),"Breslau (Wrocław)":("Wrocław",51.11,17.03),
"Glogau (Głogów)":("Głogów",51.66,16.08),"Frankfurt (Oder)":("Frankfurt (Oder)",52.34,14.55),"Küstrin":("Kostrzyn nad Odrą",52.59,14.65),
"Stettin (Szczecin)":("Szczecin",53.43,14.55),"Hann. Münden":("Hann. Münden",51.42,9.65),"Hameln":("Hameln",52.10,9.36),"Minden":("Minden",52.29,8.92),
"Bremen":("Bremen",53.08,8.80),"Schweinfurt":("Schweinfurt",50.05,10.23),"Würzburg":("Würzburg",49.79,9.95),"Aschaffenburg":("Aschaffenburg",49.98,9.15),
"Frankfurt":("Frankfurt am Main",50.11,8.68),"Hanau":("Hanau",50.13,8.92),"Rottweil":("Rottweil",48.17,8.63),"Tübingen":("Tübingen",48.52,9.06),
"Esslingen":("Esslingen am Neckar",48.74,9.31),"Stuttgart":("Stuttgart",48.78,9.18),"Heilbronn":("Heilbronn",49.14,9.22),"Heidelberg":("Heidelberg",49.41,8.71),
"Mannheim":("Mannheim",49.49,8.47),"Metz":("Metz",49.12,6.18),"Trier":("Trier",49.75,6.64),"Liège":("Liège",50.63,5.57),"Namur":("Namur",50.47,4.87),
"Maastricht":("Maastricht",50.85,5.69),"Venlo":("Venlo",51.37,6.17),"Cambrai":("Cambrai",50.18,3.24),"Tournai":("Tournai",50.61,3.39),"Ghent":("Ghent",51.05,3.72),
"Antwerp":("Antwerp",51.22,4.40),"České Budějovice (Budweis)":("České Budějovice",48.97,14.47),"Prague":("Prague",50.09,14.42),"Innsbruck":("Innsbruck",47.27,11.39),
"Kufstein":("Kufstein",47.58,12.17),"Wasserburg":("Wasserburg am Inn",48.06,12.23),"Freising":("Freising",48.40,11.75),"Landshut":("Landshut",48.54,12.15),
"Munich":("Munich",48.14,11.58),"Landsberg":("Landsberg am Lech",48.05,10.87),"Augsburg":("Augsburg",48.37,10.90),"Cottbus":("Cottbus",51.76,14.33),
"Berlin and Cölln":("Berlin",52.52,13.40),"Potsdam":("Potsdam",52.40,13.07),"Brandenburg an der Havel":("Brandenburg an der Havel",52.41,12.56),"Jena":("Jena",50.93,11.59),
"Naumburg":("Naumburg (Saale)",51.15,11.81),"Halle (salt, sign only)":("Halle (Saale)",51.48,11.97),"Rheine":("Rheine",52.28,7.44),"Lingen":("Lingen (Ems)",52.52,7.32),
"Emden":("Emden",53.37,7.21),
}
def hav(a,b,c,d):
    p=math.pi/180; x=math.sin((c-a)*p/2)**2+math.cos(a*p)*math.cos(c*p)*math.sin((d-b)*p/2)**2
    return 12742*math.asin(math.sqrt(x))
CACHE=os.path.join(os.path.expanduser("~"),"basework","wd_cache.json")
os.makedirs(os.path.dirname(CACHE),exist_ok=True)
C=json.load(open(CACHE)) if os.path.exists(CACHE) else {"search":{},"coords":{}}
def save(): json.dump(C,open(CACHE,"w"))
T0=time.time(); BUDGET=float(os.environ.get("BUDGET","95"))
class Stop(Exception): pass
def api(**kw):
    kw["format"]="json"; url="https://www.wikidata.org/w/api.php?"+urllib.parse.urlencode(kw)
    for _ in range(4):
        if time.time()-T0>BUDGET: raise Stop()
        try:
            r=urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":UA}),timeout=30); time.sleep(1.0); return json.load(r)
        except urllib.error.HTTPError as ex:
            wait=int(ex.headers.get("Retry-After","15")) if ex.code==429 else 3
            if time.time()-T0+wait>BUDGET: raise Stop()
            time.sleep(wait)
        except Exception: time.sleep(3)
    return {}
# --- frame projection (same as build_base.py) for pixel positions on the 10800 x 14400 master
a=6378137.0; f=1/298.257223563; e2=2*f-f*f; e=math.sqrt(e2); R=math.radians
def m_(p): return math.cos(p)/math.sqrt(1-e2*math.sin(p)**2)
def t_(p): return math.tan(math.pi/4-p/2)/((1-e*math.sin(p))/(1+e*math.sin(p)))**(e/2)
l1,l2,l0,lo0=44.84,53.02,48.93,10.67; XMIN,XMAX,YMIN,YMAX=-503671,504058,-661508,682131
n=(math.log(m_(R(l1)))-math.log(m_(R(l2))))/(math.log(t_(R(l1)))-math.log(t_(R(l2)))); F=m_(R(l1))/(n*t_(R(l1))**n); rho0=a*F*t_(R(l0))**n
def px(la,lo):
    rho=a*F*t_(R(la))**n; th=n*(R(lo)-R(lo0)); x=rho*math.sin(th); y=rho0-rho*math.cos(th)
    return round((x-XMIN)/(XMAX-XMIN)*10800),round((YMAX-y)/(YMAX-YMIN)*14400)
# --- manifest
rivers=[]; river=None; order=0; rows=[]
for line in open(os.path.join(ROOT,"river-manifest.md"),encoding="utf-8"):
    m=re.match(r"## \d+\. (.+?)( \(|$)",line)
    if m: river=m.group(1); order=0; continue
    m=re.match(r"\| (\d+) \| (.+?) \| (new|brief) \|",line)
    if m and river: rows.append((river,int(m.group(1)),m.group(2),m.group(3)))
print(len(rows),"manifest rows")
try:
    for place,(term,la0,lo0_) in P.items():
        if place not in C["search"]:
            r=api(action="wbsearchentities",search=term,language="en",type="item",limit=8)
            C["search"][place]=[x["id"] for x in r.get("search",[])]; save()
    need=sorted({q for ids in C["search"].values() for q in ids if q not in C["coords"]})
    for i in range(0,len(need),50):
        r=api(action="wbgetentities",ids="|".join(need[i:i+50]),props="claims")
        for q in need[i:i+50]:
            c=r.get("entities",{}).get(q,{}).get("claims",{}).get("P625")
            C["coords"][q]=[c[0]["mainsnak"]["datavalue"]["value"]["latitude"],c[0]["mainsnak"]["datavalue"]["value"]["longitude"]] if c else None
        save()
except Stop:
    save(); print("time budget reached: searched",len(C["search"]),"of",len(P),"places; run again to continue"); raise SystemExit(2)
cache={}; miss=[]
for place,(term,la0,lo0_) in P.items():
    best=None
    for q in C["search"].get(place,[]):
        c=C["coords"].get(q)
        if not c: continue
        d=hav(c[0],c[1],la0,lo0_)
        if d<25 and (best is None or d<best[0]): best=(d,q,c[0],c[1])
    if best: cache[place]=best
    else: miss.append(place)
out=os.path.join(ROOT,"river-sites.csv")
with open(out,"w",newline="",encoding="utf-8") as fh:
    w=csv.writer(fh); w.writerow(["river","order","site","status","lat","lon","px_x","px_y","wikidata","check_km","coordinate_source"])
    for river,o,place,st in rows:
        if place in cache:
            d,q,la,lo=cache[place]; x,y=px(la,lo)
            w.writerow([river,o,place,st,round(la,5),round(lo,5),x,y,q,round(d,1),"Wikidata P625"])
        else:
            la0,lo0_=P[place][1],P[place][2]; x,y=px(la0,lo0_)
            w.writerow([river,o,place,st,la0,lo0_,x,y,"","","estimate, no Wikidata match; check"])
print("matched",len(cache),"of",len(P)); print("no match:",miss)
far=[(p,round(v[0],1)) for p,v in cache.items() if v[0]>8]; print("over 8 km from estimate:",far)
