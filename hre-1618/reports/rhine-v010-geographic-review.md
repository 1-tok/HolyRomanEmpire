# Rhine v010 geographic extension review — Strasbourg north and south

**Status: review-only. NOT seam-approved or historically approved.** The v009 center section is preserved as reference and the approved v007 remains unchanged.

The locally generated v010 transparent overlay places additional north and south paintings around the v009 center on the 3600 × 4800 geographic coordinate system. It is an **artistic overlay draft**: the new watercourse bends, settlement paintings, and overlaps have not been proven consistent with the 1618 Upper Rhine.

## Coordinates and geographic approach

- Projection and pixel transform follow `tools/build_base.py` using the project's WGS84 Lambert Conformal Conic.
- Use `placements/rhine-v010-geographic-review.json` for settlement anchors, all approximate modern center points needing historical footprint review.
- Go north toward Germersheim, Speyer, Worms, Oppenheim, Mainz, Bingen, Koblenz; south through Rhinau, Marckolsheim, Breisach, Neuenburg, Basel. Keep Erstein, Benfeld and Illkirch on the **Ill-side** geography.
- Preserve existing city sprites for Strasbourg, Speyer, Worms, Mainz and Basel. New minor towns must not look as dominant as Strasbourg.
- Treat the modern Natural Earth 10m Rhine only as a provisional georeferencing control; reconcile historically before final painting.

## Local review outputs — not yet committed as binary files

- `rhine_v010_extended_geo_review_overlay.png`: transparent 3600 × 4800 registered candidate.
- `rhine_v010_target_canvas_review.html`: interactive viewer fetching GitHub's original base URL, with city anchors and seam boundaries.
- `rhine_v010_extended_review_crop.jpg`: joined north/center/south illustration with seam-review guide lines.
- `rhine_v010_geo_review.zip`: all of the above plus local manifest.

## Current QA

The two independently produced extensions **do not yet pass strict seam acceptance**. Feathered overlaps lessen hard rectangular boundaries but introduce ghosted scenery and possible water misalignment. Exact 1618 Rhine riverbanks and side channels are not certified; several painted generic villages cannot be equated with georeferenced sites without a dedicated sprite placement step.

No original images have been overwritten; do not merge v010 as approved map art. Next: generate river-only seam connector strips from known endpoints, re-register all towns, and validate the entire composite against the actual base river and Ill separately.
