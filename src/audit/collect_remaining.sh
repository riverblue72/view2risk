#!/bin/bash
set -euo pipefail
cd /data/whereami/math/view2risk_261025
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 TMPDIR="$PWD/tmp"
/data/whereami/envs/lesionlocator/bin/python -u scripts/download_imptc_remaining.py
