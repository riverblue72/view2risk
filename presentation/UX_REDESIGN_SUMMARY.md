# View2Risk User-Centered UX Redesign

Status: PASSED — implemented and verified locally.

## What changed

The first view now answers a concrete question: will this recorded pedestrian finish in the next H seconds? It shows three aligned saved probabilities, the actual recorded outcome, and a short numerical interpretation before technical panels. The default is the verified f2 origin `o0008`, not an arbitrary far-away example.

A collapsible natural-language case finder retrieves recorded situations. Guided mode uses only fully matched origins; Expert mode exposes broader records and explains missing evidence. Ordinary exploration shows GT immediately. Presentation mode hides/reveals future GT without changing the origin or predictor inputs.

The preserved Babylon renderer explains spatial paths. A separate CDF explains remaining time. A shared-axis overlay explains synthetic observation error. M0/M1/M2 comparisons are optional, separately trained model comparisons. A new Results page presents four findings rather than a catalog of unrelated charts.

## Main local URLs

- Comparison: http://127.0.0.1:18779/presentation/compare.html
- Findings: http://127.0.0.1:18779/presentation/results.html
- Presentation: http://127.0.0.1:18779/presentation/presentation.html
- Methods: http://127.0.0.1:18779/presentation/methods.html
- Preserved recording playback: http://127.0.0.1:18779/presentation/#/simulation
- Preserved detailed experiments: http://127.0.0.1:18779/presentation/#/results/trajectory

## Design references studied

These were consulted for principles, not copied branding/code:

- [Seeing Theory](https://seeing-theory.brown.edu/): visual introduction before technical detail → simple probability bars, expandable mathematics.
- [Distill: Building Blocks of Interpretability](https://distill.pub/2018/building-blocks/): coordinated explanatory interfaces → one exact observation key across model views.
- [TensorFlow Playground](https://playground.tensorflow.org/): controls tied to visible outputs → immediately updated saved scenarios; unlike Playground, this site performs no new training.
- [Our World in Data](https://ourworldindata.org/grapher/child-mortality): prominent source/units/context → per-figure cohort, horizon, units and source links.
- [The Pudding](https://pudding.cool/): question-driven visual explanation → four narrative research findings.

## Evidence and limits

The new UX passed 46 browser checks; 43 existing-route regression checks also passed. There were no uncaught JavaScript exceptions or HTTP failures. Source-level verification and an independent Python availability audit passed.

Public scope remains small: 35 saved DD origins, 6 time-model origins and 3 R origins. Empty categories are honest data limitations. Fixed display filters do not change model inputs or scientific subgroup results. A single demonstration is not proof of model superiority or calibration.

## Preservation and publication boundary

Canonical source: `/Users/gwondohyeon/view2risk_presentation_publish_20261123/presentation/site/`.
Deployment mirror: `/Users/gwondohyeon/view2risk_presentation_publish_20261123/docs/presentation/`.
The 202 static files are byte-identical across those directories. This is a local, uncommitted review revision on `presentation/synchronized-three-panel-20261123`; no push was performed. The current GitHub Pages release is unchanged.

188 previously protected files remain byte-identical, including `final/`, `docs/final/`, saved prediction/metric artifacts and the resolved historical metric audit. No model training, inference, hyperparameter selection, calibration, GT modification or new private-data export occurred. Individual replay still uses only existing allowlisted IMPTC excerpts. The website is a static replay, not a browser inference service.
