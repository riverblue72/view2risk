#!/bin/bash
#SBATCH --job-name=view2risk-full
#SBATCH --partition=batch_ce_ugrad
#SBATCH --account=ugrad_ce
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --chdir=/data/whereami/math/full_rq_261026
#SBATCH --output=/data/whereami/math/full_rq_261026/run.log
set -euo pipefail
cd /data/whereami/math/full_rq_261026
if [ -f reports/full_summary.md ]; then
    echo "Completed full-data experiment is immutable; use a new output directory." >&2
    exit 1
fi
mkdir -p tmp reports
export TMPDIR="$PWD/tmp" MPLCONFIGDIR="$PWD/tmp/mpl" NUMBA_CACHE_DIR="$PWD/tmp/numba"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
PY=/data/whereami/envs/lesionlocator/bin/python
"$PY" -u scripts/audit.py prepare
"$PY" -u scripts/audit.py spd > reports/spd_parser.log 2>&1 &
R_PID=$!
"$PY" -u scripts/audit.py imptc_set_02 > reports/set_02.log 2>&1 &
P2=$!
"$PY" -u scripts/audit.py imptc_set_03 > reports/set_03.log 2>&1 &
P3=$!
wait "$P2";wait "$P3"
"$PY" -u scripts/audit.py imptc_set_04 > reports/set_04.log 2>&1 &
P4=$!
"$PY" -u scripts/audit.py imptc_set_05 > reports/set_05.log 2>&1 &
P5=$!
wait "$P4";wait "$P5";wait "$R_PID"
test -f reports/spd_metrics.json
for part in 02 03 04 05; do test -f "parts/imptc_set_$part/audit_reuse.json"; done
"$PY" -u scripts/audit.py combine
while [ ! -f PILOT_READY ]; do sleep 5; done
"$PY" -u scripts/full_pilot.py
