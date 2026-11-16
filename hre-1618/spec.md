# Holy Roman Empire before the Thirty Years War, AD 1618 - map spec (v2)

Title cartouche: "The Holy Roman Empire / Germany, Bohemia and the Netherlands / on the eve of the Thirty Years War, AD 1618". Form: place / theme / moment.

## Daryl's choices

- Moment: AD 1618, the year before the Defenestration of Prague.
- Sheet: portrait 36 x 48 in, 10800 x 14400 px at 300 dpi.
- Frame: from Lille and the Dutch coast in the west to Breslau and Vienna in the east; Lubeck and Schleswig in the north to the Po valley in the south. Copenhagen and Rome are off the sheet.
- Netherlands: included. The Spanish Netherlands were a circle of the Empire; the Dutch Republic was still formally in it until 1648.
- Editions: colour and parchment (assumed, not yet confirmed).

## Projection and extent

- Lambert Conformal Conic, WGS84
- Standard parallels 44.84 and 53.02; latitude origin 48.93; central meridian 10.67
- Extent (m): x -503672 to 504058; y -661508 to 682132
- Metres per print pixel: 93.31
- Latitude range 42.79N to 55.06N; longitude range 2.84E to 18.51E
- Corners: NW 2.84E 54.83N; NE 18.51E 54.83N; SW 4.53E 42.79N; SE 16.82E 42.79N

## Status

- Frame and layout check drawn (frame_preview_v2.jpg).
- State placements are approximate labels, not boundaries. Real 1618 boundaries need a historical source before they are drawn.
- Route and symbol data not yet built.

## Base map underlay (built 2026-11-16)

Script: tools/build_base.py. Output: base/base_3600.jpg (3600 x 4800 px, a quarter of the 10800 x 14400 master on the same frame), base/base_preview_1200.jpg, base/borders_used.txt.

Daryl's choices: clean underlay for placing ChatGPT sprites, not the finished sheet; working size first, full master after approval; borders for the larger states only; period water on.

Layers
- Land: AWS terrarium tiles at zoom 7, height-tinted from #a7bd86 at sea level through tan to grey rock and snow, hillshade from the north-west. Land mask from Natural Earth 10m land, with Natural Earth lakes cut out.
- Sea: lighter near the coast (#7fa3b4), darker offshore (#46708b).
- Rivers: Natural Earth 10m river centrelines, fixed width (wider for the Rhine, Danube, Elbe, Oder, Vistula, Weser, Po). First pass only: no hand-drawn meanders and no minor rivers yet.
- Borders: ETH Zurich manual territories, entries active in 1618 (start 1618 or earlier, end after 1618), de-duplicated by polygon, territories over 3000 km2, fragments under 600 km2 dropped. 54 territories. Thin red-brown lines, one weight for all.
- Cities: dots only, no lettering. Red inside the Empire, grey outside. Positions are approximate.
- Period water: the Zuiderzee is drawn as sea from a hand-placed outline of its shore towns (Medemblik, Enkhuizen, Hoorn, Edam, Muiden, Spakenburg, Harderwijk, Elburg, Kampen, Stavoren). Approximate, not from a palaeogeographic source. Other changes (Frisian coast, Dollart, Baltic lagoons) are not yet made.

Known problems
- ETH polygons are deeply interlocked in the south-west and the centre (counties, imperial cities and knights' lands are cut out of the larger states), so borders there are accurate to the data but cluttered. A hierarchy (heavier for electorates, duchies and the kingdom of Bohemia) or an Imperial Circles layer would help.
- "albertinisches Sachsen (nach 1635)" has no dates in the data and stands in for Electoral Saxony. It includes Lusatia, which was Bohemian in 1618, so Saxony's east border is too far east.
- Royal Prussia and Ermland (Polish) and the Swiss and French entries are drawn with the rest. The Empire's outer edge is not yet marked.
- No land-cover layer (forest, farmland, marsh) on this underlay; the rule-based version in frame_terrain_v7.jpg is a placeholder.

Licence: borders derive from the ETH dataset (CC BY-NC-SA 4.0, Roller 2021, doi 10.3929/ethz-b-000472583). Personal, non-commercial use only; credit the dataset and keep the same licence on anything derived.
