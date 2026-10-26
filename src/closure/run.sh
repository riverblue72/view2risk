#!/bin/bash
#SBATCH --job-name=v2r-audit-close
#SBATCH --partition=batch_ce_ugrad
#SBATCH --account=ugrad_ce
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=/data/whereami/math/view2risk/runs/audit_261026/run.log
set -euo pipefail
cd /data/whereami/math/view2risk/runs/audit_261026
export TMPDIR="$PWD/tmp" TEMP="$PWD/tmp" TMP="$PWD/tmp"
export MPLCONFIGDIR="$PWD/tmp/mpl" OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
mkdir -p tmp reports figures data docs
if [ -f reports/summary.md ]; then
  echo 'Completed audit is immutable; choose a new output directory.' >&2
  exit 1
fi
/data/whereami/envs/lesionlocator/bin/python scripts/crossings.py
