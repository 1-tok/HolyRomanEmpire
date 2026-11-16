# Rhine Batch 001 — Basel, Strasbourg, Speyer, Worms, Mainz

**Target:** existing `hre-1618/base/base_3600.jpg` canvas on `main` (3600 × 4800 pixels). The base projection and river source remain unchanged.

## Files committed on this branch
- `placements/rhine-batch-001.json` — geographic site anchors and 105px working-canvas artwork size.
- `tools/build_rhine_batch001.py` — regenerates geographic river water overlays and crops them into precisely matching, non-overlapping connector sprites.
- `.github/workflows/hre-rhine-batch-001.yml` — runs the renderer and publishes QA images as a downloadable Actions artifact.

## PNG assets to upload
The companion `hre1618_rhine_batch001.zip` contains the **five original individual RGBA images**, plus the independent placement/build package. Upload exactly these five PNGs from its `sprites/` directory to `hre-1618/sprites/` in this repo:

1. `Basel.png`
2. `Strasbourg.png`
3. `Speyer.png`
4. `Worms.png`
5. `Mainz.png`

These PNG binaries are **not yet in the repository**. Do not claim that their placement has been rendered until the workflow has run with all five present.

## Building
`python3 -m pip install Pillow`

`python3 hre-1618/tools/build_rhine_batch001.py`

Or run the `HRE 1618 Rhine Batch 001 placement QA` action after placing the PNGs.

Output is in `hre-1618/reports/rhine-batch-001/`, including:
- `on-existing-base-3600.jpg` — visual QA on the existing canvas.
- `continuous-rhine-water-overlay.png` — one geographic river layer.
- `connector-01.png` ... — non-overlapping pieces cut from that single geographic layer. Their world x/y offsets are recorded in `placements.json` and must be respected when reassembled.
- `placements.json` — rendered image placement coordinates.

## Historical and rendering limits
This is a provisional QA process, not a finalized historical river reconstruction. The Natural Earth 10m Rhine centerline follows the source used in the repository base, but may differ from the watercourse in 1618. The city paintings also show stylized riverbanks, quays and bridges; their painted water is masked where it would interrupt the base course. Bridges require separate historically grounded overlay positions.

**Never manually bend the reference river to join city artwork.** The city art must be masked or adjusted to the fixed river. Strasbourg is on the Ill, west of the Rhine, and must not be moved onto the Rhine itself. No automatic promotion to the print master until 1618 historical QA and 225px @ 300dpi legibility review.
