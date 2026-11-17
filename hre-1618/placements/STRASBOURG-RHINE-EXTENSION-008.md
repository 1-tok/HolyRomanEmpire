# Strasbourg Upper Rhine expansion — placement and sprite production brief (AD 1618)

**Status:** approved visual approach; HISTORICAL AND PRINT QA PENDING. This is an actionable generation and placement queue, **not a claim that the extension artwork already exists**.

## Fixed canvas and existing pilot
- Branch: `artwork/rhine-city-batch-001`
- Working base: `hre-1618/base/base_3600.jpg` (3600 × 4800).
- Historic extent/projection: `hre-1618/spec.md`, Lambert Conformal Conic.
- Existing approved visual reference: `hre-1618/maps/canvas/strasbourg-painted-rhine-006.jpg`.
- Map-scale Strasbourg preview: `hre-1618/maps/canvas/strasbourg-approved-painted-preview-007.jpg`.
- Existing three-piece Strasbourg painting coverage: y ≈ 2396–2708 (see `reports/strasbourg-approved-placement-007/qa.json`); city anchor (1032.33,2563.33). Its artistically depicted river course is **not yet a verified Ill–Rhine 1618 reconstruction**.
- Preserve source art and v006/v007 files untouched. Do not duplicate established Strasbourg or other approved city sprites.

## River/scenery extension queue
| ID | Direction | Target canvas region (approximate, pixels) | Requested artwork | Blend and QA |
|---|---|---|---|---|
| RHE-N01 | north | x 960–1190, y 2290–2440 | braided Rhine reaches, islands, gravel/sand bars, riparian forest | overlap v007 northern painted edge at y 2396; align with mapped course; no abrupt river width jump |
| RHE-N02 | north | x 950–1200, y 2170–2340 | continuation toward Upper Rhine cities, narrow marsh corridors and meanders | preserve Speyer/Worms candidate city layers; do not paint over their foregrounds |
| RHE-S01 | south | x 850–1160, y 2660–2825 | Rhine floodplain channels, historic ferry banks, marsh and meadow | overlap v007 southern painted edge at y 2708; do not represent Strasbourg city as sitting on main Rhine |
| RHE-S02 | south | x 820–1150, y 2780–2960 | wooded islands, wet meadow and riverbank continuation toward Basel | layer behind existing Basel sprite; preserve existing water and mountain/terrain layers |

**Coverage rectangles are art production windows, NOT proven historical channel geometry.** Before rendering, trace the actual 1618 main Rhine and Ill on their distinct courses; use the modern underlay only as provisional registration. Each reach should be separated into independently transparent overlapping pieces, with 16–32 px feathering as needed and continuous painted water through the seams.

## Settlements and landmarks queue

Reference candidate point `(x, y)` is the projected location on the working canvas, **not the top-left of the sprite**. These are approximate cartographic anchors derived from approximate modern location coordinates and the map projection; re-georeference from a period source before final approval.

| Site | Candidate point | Priority/class | Artwork and historical guardrails |
|---|---|---|---|
| Robertsau (Ruprechtsau), north/east of Strasbourg | (1043,2551) | minor hamlet/scenery | small riverside farm/fishery and alluvial woodland, not a modern suburban district; leave Strasbourg art unobstructed |
| La Wantzenau (Wantzenowe) | (1053,2531) | village | compact medieval river fishing settlement beside the Ill floodplain; keep main Rhine separate |
| Kilstett | (1061,2523) | small hamlet, historical corroboration pending | few rural roofs on drier ground; do not assert a 1618 ferry or major parish complex without evidence |
| Gambsheim | (1068,2517) | village | known pre-1618 meander settlement with meadow/fields and Rhine access; avoid imagery from later 1622 destruction |
| Illkirch | (1022,2582) | village | village on the **Ill**, not the Rhine; small church, cottages, fields, woodland |
| Erstein | (1006,2622) | minor town | historic Ill-side town and floodplain; no speculative 1618 large fortress |
| Benfeld | (987,2642) | fortified minor town | walled settlement and modest period defenses; verify exact 1618 walls, separate from main Rhine bank |
| Rhinau | (1016,2664) | village | show flood-affected, partly shifted 16th-century settlement on Rhine floodplain; precisely locate against historical source |
| Marckolsheim | (971,2724) | fortified small town | 14th-century walled town; verify shape and orientation, river side channels and flood terrace |

**Do not place all of these as same-size major city icons.** Subordinate villages should be roughly 28–50 working pixels across; minor towns 50–75 px; existing Strasbourg major city art remains dominant (~198 px scenic city-water section). Footprints are provisional and must be adjusted to local map density. Sites within existing artwork should use small inset icons or be omitted when the painting already depicts them.

## Marsh, forest and riverbank terrain underlays
- **WET-N01**: Robertsau–La Wantzenau alluvial forest (willow, alder, oak), wetlands, side channels; under village sprites.
- **WET-N02**: Gambsheim meander floodplain, wet meadow, reeds, small islands and ponds.
- **WET-S01**: Illkirch–Erstein Ill valley water meadows and intermittent marsh. Keep the Ill as its own river.
- **WET-S02**: Benfeld–Rhinau Grand Ried floodplain with reeds, wet pasture, alder/willow woodland, oxbows.
- **WET-S03**: Rhinau–Marckolsheim Rhine floodplain, braided channels, shoals, floodplain forest and dry terrace fields.

Paint terrain **as textured translucent RGBA underlays**, feathered into the current base. The art should distinguish water, marsh, flooded woodland, meadow, and settled cultivated land. No modern canal walls, engineered straightened Rhine channel, locks, hydroelectric stations, or post-1618 structures.

## Evidence register
- La Wantzenau municipal history (fishing community, Honau association and early place name): https://www.la-wantzenau.fr/Decouvrir/Histoire-ville.html
- Gambsheim municipal history (748 charter, meanders, fields, meadows, island monastery; pre-Thirty Years War record): https://mairie-gambsheim.fr/presentation-du-village/histoire-de-la-commune/
- Illkirch city history (documented before 1618, Ill-side village): https://www.illkirch.eu/votre-ville/decouvrir-la-commune/lhistoire-de-la-ville/
- Benfeld city history (medieval walls and bishopric): https://www.benfeld.fr/decouvrir/12871
- Marckolsheim municipal history (early settlement and medieval fortifications): https://www.marckolsheim.fr/Votre-ville/Presentation/Marckolsheim-fil-temps.html
- Robertsau–Wantzenau wetland history; later historical analog **not a 1618 survey**: https://reserves-naturelles.strasbourg.eu/foret-de-la-robertsau/decouvrir/
- Alsace Rhin–Ried–Bruch historical floodplain study (includes later maps; do not read 1837 courses as 1618): https://www.grand-est.developpement-durable.gouv.fr/IMG/pdf/DOCOB_RRB_S4_DOCOB_complet_cle1df826.pdf
- Bas-Rhin departmental archival plan c.1450 of Honau/Wantzenau and named marsh/field parcels, a particularly valuable pre-1618 spatial control: https://archives.bas-rhin.fr/eCommunityDocuments/996A4DC5-7B41-4352-A704-F3DF616B220D/208/Fiche%208%20-%20Cartorcodes-documents.pdf

**Evidence tiers:** existing settlements and general floodplain environment are documented; exact banklines, marsh boundaries, village footprints and 1618 channels are *provisional reconstructions*. Later historical and modern environmental sources establish landscape plausibility, not surveyed 1618 shoreline.

## Deliverables and gates for next render
1. Generate north and south RGBA painted river reaches, side-channel snippets and 5 terrain underlays. Use the approved v006/v007 painting as visual reference, not as an infallible river map.
2. Produce individual settlement PNGs only when an approved sprite for that place does not already exist; preserve side-from-above/southern viewpoint and appropriate water-side orientation.
3. Generate **placement manifest** with exact file paths, PNG SHA-256, projected anchors, dimensions, z-index, historical evidence link, and approval status.
4. Compose v008 Strasbourg expanded full-map preview and a crop large enough to inspect *both* north/south seams. Do not touch the original v007.
5. Perform QA: river vs Ill distinction; pass both transitions; transparency and alpha; no opaque boxes; map-scale footprint; terrain under cities, labels above; historical 1618-only buildings; no duplicate icons.
6. Keep print_approval=false until river/shoreline history and the visual QA pass.

**Render order:** base → wetland/forest underlays → main/side river scenes → small features/roads/ferries (only documented) → town/city/fortification sprites → all labels.
