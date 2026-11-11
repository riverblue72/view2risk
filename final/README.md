# Final View2Risk

The final predictor is the official pretrained DD-MDN, with IMPTC Full and inD Full checkpoints. We do not train or redistribute these checkpoints. Older neural experiments remain preserved elsewhere in this repository.

- [Public Simulation](../docs/final/index.html) · [Modeling Guide](../docs/final/modeling.html)
- [Methodology](METHODOLOGY.md) · [Results](FINAL_RESULTS.md) · [R decision](R_UQ_FINAL_DECISION.md)
- [Data and licensing policy](DATA_POLICY.md) · [Third-party sources](THIRD_PARTY.md)

## Source organization

`src/` contains our original analysis/inference integration snapshots: frozen-checkpoint loading, Gaussian-mixture/HDR summaries, semantic first passage, FilterPy/FFBS and PedPy analysis. These are research functions, not a new model or a public inference service. Official preprocessing and licensed datasets must be supplied separately. `tools/` records the public-site export/build steps; these require the private working tree and are not required to serve the exported website.

For private reproduction, clone the official DD-MDN at commit `0726eb14babe78349da03a4d8bdf34fb91612ebc`, install its documented environment, obtain its official checkpoints through the authors, and set `DDMDN_REPO`, `DDMDN_MODEL_ROOT`, and `VIEW2RISK_WORKDIR`. The model root must contain official `full/*_full` configuration/checkpoint directories. Supply the existing Train-fitted SPD `configs/r_proxy.json` in that work directory; no private paths or data are distributed. Run these modules with `final/src` on PYTHONPATH. Keep external assets outside Git. Never re-fit on Test.

## Static preview

From repository root: `python3 -m http.server 8000 --directory docs`. Open `http://localhost:8000/final/`. No API, Python inference service, login or GPU is required. All public predictions are existing DD-MDN outputs. The public replay is a small noncommercial IMPTC-derived demo, not a new independent test. inD is aggregate-only.

The 10 observed positions span 0.9 seconds at 0.1-second spacing; the 8 future positions occur at 0.5-second spacing through 4 seconds. Hypothesis confidence scores are not normalized event probabilities. IMPTC Exit probabilities remain Simulation-only; inD semantic Exit probabilities are not computed.
