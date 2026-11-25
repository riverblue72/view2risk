# View2Risk — Presentation Website

기존 `final/` 및 `docs/final/`과 독립된 발표용 공개 웹사이트입니다.

**[발표 시작](https://riverblue72.github.io/view2risk/presentation/)** · **[기록 기반 시연](https://riverblue72.github.io/view2risk/presentation/demo.html)** · **[Methods & Mathematics](https://riverblue72.github.io/view2risk/presentation/methods.html)** · **[Observation Noise Lab](https://riverblue72.github.io/view2risk/presentation/?case=o0008#/noise)** · **[Results](https://riverblue72.github.io/view2risk/presentation/#/results/trajectory)**

> 현재 발표 구성, 수치 출처, 브라우저 검증은 [PRESENTATION_REDESIGN_REPORT.md](../PRESENTATION_REDESIGN_REPORT.md)에 있습니다.

## Folder separation

| Path | Purpose |
|---|---|
| `presentation/site/` | Canonical static presentation source and allowlisted saved outputs |
| `presentation/tools/` | Export, static verification and browser regression scripts |
| `presentation/PUBLICATION_CHECK.md` | Public release scope and checks |
| `docs/presentation/` | Byte-identical deployment copy for the existing main `/docs` Pages configuration |
| `final/`, `docs/final/` | Prior project/release; unchanged |

The existing repository homepage and Pages configuration are unchanged. Open `/view2risk/presentation/` for this release.

## What runs publicly

- Korean eight-scene presentation with keyboard navigation, speaker notes and a pinned real example.
- Unified spatial and temporal replay of three saved IMPTC examples (f1/f2/f3), with actual DD-MDN forecasts and optional GT.
- Recorded rolling origins; DD-MDN is the default trajectory predictor. XGBoost and AFT are separate completion-time comparisons where stored outputs exist.
- Same-event/same-origin observation-noise comparison: three public R packets with saved IID, correlated-noise and dropout scenarios.
- Aggregate results, mathematical explanations and historical-route compatibility.

**This static site performs no model inference or training.** An unavailable origin/scenario is not replaced with fabricated output. The public case collection is smaller than the research evaluation cohorts; cohort metrics must not be interpreted as metrics of these three demonstration cases.

## Data and scientific limits

IMPTC-derived excerpts and stored prediction artifacts carry CC BY-NC 4.0 attribution; see [DATA_POLICY.md](site/DATA_POLICY.md) and [provenance.json](site/data/public/provenance.json). Original IDs are replaced and acquisition times made relative. World coordinates and probabilities remain intact; this is not an anonymity guarantee.

inD is **aggregate-only**: no individual trajectories, recoverable per-origin records or camera maps are distributed. No checkpoints, native raw datasets, credentials, or private Python API are included.

Completion probabilities are simulation-based and not independently population-calibrated. Historical Test reuse, limited independent dates and sparse behavioral groups remain limitations. Exit-aware XGBoost repaired its own training-support gap; this does not establish superiority over every baseline or isolated acceleration/crowding benefits.

## Local preview

From the repository root:

```sh
python3 -m http.server 18779 --bind 127.0.0.1 --directory docs
```

Open `http://127.0.0.1:18779/presentation/`. Use HTTP rather than `file://` because the site fetches local JSON. No Python backend, GPU, private network or model download is required. Babylon.js and KaTeX assets are bundled.

## Updating this presentation only

Edit `presentation/site/`, then synchronize only the new deployment directory:

```sh
python3 presentation/tools/verify_static.py --sync
python3 presentation/tools/verify_static.py
```

Do not copy these files over `final/` or `docs/final/`. The exporter reads a private research project only when explicitly invoked:

```sh
python3 presentation/tools/export_site.py /path/to/private/final_uq /path/to/new/empty/export
```

Review the export allowlist and license attribution before publication; do not publish an unrestricted server directory. Browser testing uses a running Chromium CDP endpoint (default `http://127.0.0.1:18776`):

```sh
node presentation/tools/browser_check.mjs
```

The script tests a local static HTTP server by default. Set `V2R_PUBLIC_URL` to the deployed `/presentation` URL to verify GitHub Pages. See [PUBLICATION_CHECK.md](PUBLICATION_CHECK.md) for executed evidence and [THIRD_PARTY.md](THIRD_PARTY.md) for attribution.


## Historical seven-scene research presentation

The previous release used [Presentation](https://riverblue72.github.io/view2risk/presentation/), followed by [Methods](site/methods.html), [recorded-case comparison](site/compare.html) and [Results](site/results.html). That presentation followed problem → operational GT → parallel predictors → observed outcome → synthetic observation error → three aggregate findings → contribution and limits.

Read [Storyboard](FINAL_PRESENTATION_STORYBOARD.md), [Methods](FINAL_METHODS_EXPLANATION.md), [Simulation UX](FINAL_SIMULATION_UX_REPORT.md), [Results interpretation](FINAL_RESULTS_INTERPRETATION.md) and [Browser verification](FINAL_BROWSER_VERIFICATION.md). Review screenshots and aggregate-only evidence are under `review/`.

This public site replays allowlisted saved outputs. Predictions are not model accuracies. XGBoost forecasts remaining time, DD-MDN forecasts trajectories, and R is an optional synthetic observation-noise analysis. Previous `final/` and `docs/final/` releases remain separate.
