# Reproduction

The `src/` directories contain the server-validated source snapshots. Their scripts expect the original experiment layout and dataset paths. Use a new workspace to construct that layout; only paths are replaced, not model equations or metrics.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python tools/materialize.py --workspace /absolute/path/to/new/math
```

The CPU environment was Python 3.11; exact versions are in `requirements.txt` and `reproducibility/`. A completed experiment must not be overwritten.

Download the provider's public releases according to `docs/plans/`. Full R uses all SPD infrastructure annotations/calibrations and infrastructure images; Full Q uses IMPTC Full Sequence Sets01–05. Do not pool IMPTC Samples with Full sets. TFD is Example-only and kept separate. Place raw files at the paths specified by the stage scripts. Full SPD point clouds and vehicle images are not required for this paired-annotation audit.

Stages:

1. `view2risk_261025/scripts/`: raw parsers and original sample/Set01 audits. Run the source audits in their original stage working directories; inspect each script's input requirements before starting downloads.
2. `view2risk_261025/pilot_rq_261025/scripts/`: original sample pilot. Existing sample results are not silently replaced by full-data runs.
3. `full_rq_261026/run.sh`: full audit and R/Q pilot, grouped by intersection/date. Read the frozen protocol first. The script uses Slurm; its partition/account/resources must be adapted to the local cluster. Some historical scripts retain readiness gates and require generated outputs from preceding stages.
4. `view2risk/runs/audit_261026/`: `scripts/explore.py` obtains reference code and builds map registration; `run.sh`, `run_remaining.sh`, and `run_review.sh` generate crossing, calibration, and review evidence. The official semantic PLY map must be downloaded to `full_rq_261026/assets/imptc_ground_plane.zip`. Copies of the two input plans must be placed under the closure `docs/` directory. `scripts/finalize.py` checks the original manifests/source hashes; it is a server-snapshot handoff verifier, not a generic rerun finalizer. Expected legacy checksums and fixed cohort counts deliberately refer to the recorded run and must not be used to certify a different data version.

`tools/materialize.py` prepares files only. This is a research snapshot with documented paths, dependencies and frozen outputs, not a one-command dataset-independent benchmark. `reproducibility/` records the executed run's checks; generated fresh runs require their own hashes and validation.

Raw data, per-observation Parquet, full per-track exports, source-image illustrations, video, model checkpoints and transient logs remain server-only.
