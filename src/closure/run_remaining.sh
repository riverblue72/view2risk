#!/bin/bash
#SBATCH --job-name=v2r-audit-evidence
#SBATCH --partition=batch_ce_ugrad
#SBATCH --account=ugrad_ce
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --output=/data/whereami/math/view2risk/runs/audit_261026/remaining.log
set -euo pipefail
cd /data/whereami/math/view2risk/runs/audit_261026
export TMPDIR="$PWD/tmp" TEMP="$PWD/tmp" TMP="$PWD/tmp"
export MPLCONFIGDIR="$PWD/tmp/mpl" OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
/data/whereami/envs/lesionlocator/bin/python scripts/remaining.py
