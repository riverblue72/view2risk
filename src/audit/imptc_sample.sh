#!/bin/bash
set -euo pipefail
cd /data/whereami/math/view2risk_261025
export PYTHONDONTWRITEBYTECODE=1 TMPDIR="$PWD/tmp" MPLCONFIGDIR="$PWD/tmp/matplotlib" OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VIEW2RISK_STAGE=samples
/data/whereami/envs/lesionlocator/bin/python -u scripts/02_inspect_imptc.py
