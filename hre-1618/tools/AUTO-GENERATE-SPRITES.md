# Automated HRE 1618 sprite generation (opt-in)

The generation workflow is **separate** from the proven ZIP extraction workflow.

## What it does

1. Reads the existing `hre-1618/river-sites.csv` and `hre-1618/prompts/rhine.md`.
2. Selects the first Rhine subject without an approved PNG or candidate (or uses an explicitly named site).
3. Requests **one independent 1024×1024 transparent PNG per subject** from OpenAI's Images API using the locked elevated south-facing style prompt.
4. Checks decoding, size, alpha and transparent area.
5. Commits the results to `hre-1618/sprites/candidates/`, alongside per-sprite generation metadata in `hre-1618/reports/generation/`.
6. Publishes an Actions artifact for review.

**No generation runs automatically or on a schedule.** This is intentional because API calls incur charges and artwork requires visual QA. A human must dispatch it. A maximum of three images may be requested per run.

## Activation (once)

- Configure the repository Actions secret `OPENAI_API_KEY` in GitHub → Settings → Secrets and variables → Actions.
- Use a key with permission to call the chosen image model and billing configured. GitHub Actions has its own usage costs in addition to the OpenAI API.
- The workflow must exist on the branch where it is run. If it isn't offered in GitHub's Actions menu, make it available on the default branch first.

## Run

Open **Actions → HRE 1618 — Generate Rhine sprite candidates → Run workflow**.

- **Branch:** `artwork/rhine-city-batch-001`, which contains Basel/Strasbourg/Speyer/Worms/Mainz already accepted.
- **Count:** 1 to 3. Select 1 for the first run.
- **Site:** leave blank for the next missing Rhine subject (Koblenz after the initial five), or enter an exact name from the manifest.
- **Model:** `gpt-image-2.5-flare` is the fast option; `gpt-image-2.5-sunburst` is the refinement option.

Candidates deliberately do **not** go into `sprites/` as approved assets, do not overwrite existing PNGs, and do not alter the river geometry of `base/base_3600.jpg`.

## Approval sequence

Inspect each candidate at **225px** (3/4 inch at 300 DPI) and against its 1618 architectural landmark references. Verify south-facing POV and that riverside structures are on the historically correct bank. The trusted geographic base retains the watercourse: mask candidate water on overlay instead of bending that river. After review, promote the PNG from `sprites/candidates/` into `sprites/` and update the manifest.

## Important limitations

- An image model does not guarantee historical architecture, identical reference-image aesthetics, or pixel-perfect water alignment just from a text prompt.
- The approved style is specified textually. For closer fidelity, use an authorized image-edit/reference-image request and a stored image reference in a later improvement.
- Site coordinates are anchored by the repository but the image itself contains no georeferencing; placement is still a separate QA step.
- For truly unattended scheduled generation, add an explicit schedule and spending limit only after at least one approved manual run.
