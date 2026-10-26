#!/bin/bash
set -euo pipefail
cd /data/whereami/math/view2risk_261025
export PYTHONDONTWRITEBYTECODE=1 TMPDIR="$PWD/tmp" MPLCONFIGDIR="$PWD/tmp/matplotlib" OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VIEW2RISK_STAGE=main
for step in $(seq 1 180); do
  if test -f data/raw/imptc_set_01/extraction_complete.json; then
    /data/whereami/envs/lesionlocator/bin/python -u scripts/02_inspect_imptc.py
    exit 0
  fi
  if test -f reports/downloads/imptc_set_01_parallel_error.json; then
    cat reports/downloads/imptc_set_01_parallel_error.json
    exit 1
  fi
  sleep 10
done
exit 2
