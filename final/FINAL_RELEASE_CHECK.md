# Final public release check — 2026-11-11

## PASSED

- Existing tracked files remain byte-identical, excluding additive README introduction. Original README body remains complete. No deletion, force push or history rewrite.
- Static docs/final with relative paths, local Babylon.js/KaTeX and no private API dependency.
- Actual pretrained IMPTC outputs: three licensed excerpts. Mixture probabilities differ from unnormalized hypothesis confidence.
- Q-only default; R+Q opt-in; eight past FFBS histories. Relative +8s uses origin +8s.
- Desktop 1600px and mobile 390px: no overflow, missing images, runtime exceptions or equation errors. Guide: 8 chapters, 48 A–F subsections and 21 rendered equations, valid anchor links.
- Actual full-Test metrics separate from exploratory R/Calibration results.
- No weights, credentials, private API or inD reconstructable data exported.
- Private server Guide installed separately; index backed up before menu addition. Original model/data/results preserved.

## LIMITATION

- Three precomputed IMPTC demo cases are not independent benchmark evidence. Data license: CC BY-NC 4.0.
- inD publicly aggregate-only; schematic ground is not a camera map.
- IMPTC Exit probabilities remain Simulation-only; inD semantic Exit probabilities are not computed.
- R+Q is not consistently superior to Q-only. Small-subset exploratory results do not establish generalization.

GitHub Pages deployment is checked separately after push. No new model training or experiment performed.
