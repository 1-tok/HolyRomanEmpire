# Automatic sprite ZIP intake — HRE 1618

GitHub Actions workflow: `.github/workflows/hre-sprite-extract.yml`.

## Upload method

Upload **any ZIP** into `hre-1618/` or a nested folder on the branch on which you want the individual PNGs committed. The ZIP can contain multiple nested folders (e.g. `sprites/Basel.png`); only PNG image members are extracted.

GitHub Actions starts when ZIP files are pushed; for ZIPs uploaded before the workflow existed, choose **Actions → HRE 1618 — Auto-extract sprite uploads → Run workflow**, selecting the branch containing the ZIP. The pipeline scans *all* ZIPs under `hre-1618/`, so old batches can be safely replayed.

## Results

- Accepted PNG files: `hre-1618/sprites/<name>.png`
- Registry: `hre-1618/sprites/manifest.csv`
- Per-archive QA report: `hre-1618/reports/intake/<zip-name>-<sha12>.json`
- GitHub Actions run artifact: reports for convenient inspection.

The workflow commits accepted files and reports to the **same branch** as the incoming upload using `github-actions[bot]`, not to a different branch or directly to `main` (unless the ZIP was uploaded on `main`).

## Acceptance checks

- Actual PNG image, decoded successfully with Pillow.
- Square canvas, at least **1024 × 1024** and at most 12000 × 12000.
- Transparent alpha channel with some genuinely transparent pixels.
- SHA-256 deduplication, including duplicates across previously ingested archives.
- Safe ZIP members (no traversals, absolute paths or symlinks).
- Archive limit 100 MB, unpacked limit 250 MB, member limit 45 MB per PNG.
- Name conflicts with different contents are **reported, never overwritten**.

Non-PNG material (CSV, JSON, scripts, placement notes) stays inside the original ZIP; these are not automatically executed. Archives are **not deleted**. Rejected images and conflicts stay inside the original ZIP, and reasons appear in the QA report.

**Important:** Extraction validates the file format, not historical accuracy or whether a city sprite is on the correct side of the Rhine. Placement requires separate visual/map-scale approval. The optional Rhine overlay uses the existing base canvas.

## Technical notes

This workflow does not depend on ChatGPT Work. It runs with standard GitHub-hosted Actions, Python 3 and Pillow. If branch-protection disallows bot pushes, it will fail at the commit step, and repository Actions permissions must be adjusted. Actions triggered by bot commits do not normally retrigger the other workflows automatically; run the Rhine preview manually or review the preview uploaded by the intake workflow.

This pipeline currently handles `hre-1618/`, not other projects (e.g. `ottonian-reich-1000/`) without changing the scope.
