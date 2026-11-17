# Strasbourg Batch 008 — local preflight QA, 2026-11-17

**Decision: HOLD / NOT SEAM-APPROVED.** GitHub connector read/push permissions confirmed, but the two locally generated paintings have not been validated against the approved v007 source pixels.

## Actual local PNG inspections
| Candidate | PNG dimensions | Fully transparent pixels | Fully transparent share | SHA-256 |
|---|---:|---:|---:|---|
| a_detailed_hand_painted_isometric_illustrated_map.png | 1024 × 1536 | 344318 | 21.89% | `5837ab225cf9d3943fc7a966bd8f326b31d44e962cbe8dba11452fa3182da8d0` |
| a_detailed_painted_isometric_illustrated_cartograp.png | 1536 × 1024 | 423361 | 26.92% | `906d56205356c58938925f87e8a82d4f8a4fbac7da414939b022bd07b1b5e2f6` |

Both images have partial alpha (maximum alpha value 254). Their transparent backgrounds are **not evidence of a seamless joint**. They were generated as scenic concepts rather than from exact port geometry, matching water cross-sections, or preexisting 3-piece segment boundaries.

## Existing approved attachment and QA control
- `hre-1618/reports/strasbourg-approved-placement-007/qa.json`
- Existing painting occupies approximately y=2396..2708 on 3600×4800 canvas. Existing city center anchor (1032.33,2563.33).
- Existing painting's cross-segment seams had passed locally at earlier stage; those checks do **not** transfer to new candidates.
- No north or south fitting, image-to-image composite, or water/bank pixel seam test of the *new* PNGs has passed.

## Acceptance conditions before committing binary artwork as approved
1. Obtain existing approved v007 RGBA overlay in the same local image processing runtime (not just its JSON metadata).
2. Extract genuine north/south river artwork from the candidates (village/city scenery detached as necessary). Register water endpoints and map scale to the existing v007 segments.
3. Compare cut-edge continuity: water intersects both adjoining edges; no gaps or white seams; river width and bank direction follow; marshland edges transition naturally; no abrupt duplicate city/castle imagery.
4. Render a local Strasbourg-area joint overlay and at least one 1:1 scale crop for inspection; record image dimensions, transforms, alpha QA, and seam test findings.
5. On success commit *candidate* painted PNGs and preview to a review branch. Promote to accepted main map only after user visual approval.

This report records only **preflight inspection**. No new assets are approved, no existing approved art was overwritten, and no seamless continuity is claimed.
