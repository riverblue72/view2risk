# Public presentation release check

Date: 2026-11-23. Status: local static release checks PASSED; live deployment is verified after push.

## Isolation and deployment

- Added paths only: `presentation/` and `docs/presentation/`.
- Existing Pages source: branch `main`, `/docs`; no configuration change.
- Original repository base: `3cf94f1e9eef6f802c9287138eaf96bb6052aff0`.
- Preserved `final/` tree: `70c9e0fb3449bdd06c8f90dfe2aa44afd602ca95`.
- Preserved `docs/final/` tree: `f67b7d315de034fe4853e051b05d69025f0c8632`.
- Source and Pages copies: 193 byte-identical files verified by SHA256.
- No source experiments, checkpoints, training jobs or private server routes changed.

## Executed browser verification

Local nested hosting URL: `http://127.0.0.1:18779/presentation/`.

**47/47 checks passed; zero uncaught JavaScript exceptions; zero HTTP error responses.** Chromium with cache disabled; desktop 1440×900, responsive widths 756 and 390 pixels. Evidence: [checks/local_browser_check.json](checks/local_browser_check.json).

Verified actual playback and pedestrian movement, rolling-origin advancement, current-origin probabilities, pinning and seeking, unavailable forecast clearing, GT reveal/hide, f1 case selection, fixed presentation event/origin, keyboard navigation, 10 methods chapters and rendered equations, all five R scenarios at the same origin, results tabs, legacy anchors, Modeling Guide aggregate loading and mobile overflow.

The selected presentation case remains `public-imptc-01`, relative origin +8s, stored DD-MDN H3 probability 0.6625. This is a stored prediction, not an educational invented value. Numeric R checks compare the rendered H4 value with the corresponding saved packet.

Initial export checks found a legacy Modeling Guide JSON path and an omitted private CSV link. Both were corrected in the new presentation export. The private origin CSV was not published; its link now points to public provenance. No missing literal local links remained at release review.

## Public scope and limitations

Three licensed IMPTC excerpts, 35 saved rolling origins total, three matched R packets. The case explorer has a smaller subset of origins with matched completion estimators. The existing aggregate research cohorts remain distinct from these demonstration counts.

Only saved modes are selectable. Private inD per-origin records, reconstructable tracks/maps, checkpoints and credentials are excluded. inD figures contain aggregate statistics only. IMPTC attribution is retained under CC BY-NC 4.0. Public IDs and relative timestamps reduce exposed metadata without claiming anonymity.

Server-side inference and full private case catalogs are intentionally unavailable on Pages. Historical Test reuse, short forecast support, unvalidated population completion calibration and optional R transfer assumptions remain limitations.

## Reproduce

```sh
python3 presentation/tools/verify_static.py
python3 -m http.server 18779 --bind 127.0.0.1 --directory docs
node presentation/tools/browser_check.mjs
```

Expected deployment: https://riverblue72.github.io/view2risk/presentation/ . Existing site remains under its original routes.
