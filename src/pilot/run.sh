#!/bin/bash
#SBATCH --job-name=view2risk-pilot
#SBATCH --partition=batch_ce_ugrad
#SBATCH --account=ugrad_ce
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=01:00:00
#SBATCH --chdir=/data/whereami/math/view2risk_261025
#SBATCH --output=/data/whereami/math/view2risk_261025/pilot_rq_261025/run.log
set -euo pipefail
cd /data/whereami/math/view2risk_261025
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
export TMPDIR=/data/whereami/math/view2risk_261025/pilot_rq_261025/tmp
export MPLCONFIGDIR="$TMPDIR/mpl"
export NUMBA_CACHE_DIR="$TMPDIR/numba"
mkdir -p "$TMPDIR" "$MPLCONFIGDIR" "$NUMBA_CACHE_DIR"
/data/whereami/envs/lesionlocator/bin/python -u pilot_rq_261025/scripts/pilot.py
