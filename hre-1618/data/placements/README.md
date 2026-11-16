# Rhine sprite placement — AD 1618 (working baseline)

This branch establishes sourced geographic anchors before painterly tiles are placed.

## Current status
- The Rhine centerline from the Basel vicinity to the Waal/Merwede vicinity is digitized from **Natural Earth 1:50m** generalized river centerlines. This geometry is **not** an exact seventeenth-century reconstruction.
- Basel, Breisach, Strasbourg and Speyer are registered as provisional city-sprite anchors. Their previously generated four-panel concept sheet **is not yet split into approved individual transparent PNG assets**.
- Other city anchors are preparatory placeholders only, not artwork.
- **Strasbourg is on the Ill, not directly on the modern Rhine bank.** Do not snap its cathedral or city onto the Rhine itself.
- The historical Netherlands delta is **not** completed. The Pannerdens Kanaal (~1707), Nieuwe Merwede (nineteenth century) and Nieuwe Waterweg (nineteenth century) must not be painted into the 1618 map as if they existed.
- The main Waal–Merwede route, and subsidiary IJssel, Nederrijn/Lek and Oude Rijn networks, require period-specific archival validation; the coastal endpoint should not be fabricated.

## Placement / QA rules
1. Use `data/placements/rhine-reference-geometry.geojson` as a **reference** only; build a higher-resolution, historically checked waterway geometry before final 300-dpi export.
2. Keep every city sprite independent from river underlays; city and label layers render above river and terrain.
3. Preserve sprite-view orientation: elevated, south-facing oblique painting with **no horizon**, 1618 structures only.
4. Clip painted terrain against the validated riverbank; do not let land overlays cross or paint over water.
5. Each accepted sprite should be a transparent 1024 × 1024 or larger PNG with a single subject; validate 225px-downscaled print legibility (3/4 inch at 300dpi).
6. Before merging, verify river entry/exit points of adjoining tiles and city-bank relationships.
7. Do not treat the river corridor vignette composites as georeferenced source geometry.

## Reference
Natural Earth (public domain): https://github.com/nvkelso/natural-earth-vector/blob/master/geojson/ne_50m_rivers_lake_centerlines.geojson

Historical river distributaries and the Netherlands delta require independent archival support. The separate Basel, Breisach, Strasbourg and Speyer sprites are **provisional** until artwork QA.
