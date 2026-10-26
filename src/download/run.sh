#!/bin/bash
#SBATCH --job-name=view2risk-inputs
#SBATCH --partition=batch_ce_ugrad
#SBATCH --account=ugrad_ce
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=04:00:00
#SBATCH --chdir=/data/whereami/math/Public-V2X-Datasets
#SBATCH --output=/data/whereami/math/Public-V2X-Datasets/collection_261026/run.log
set -euo pipefail
cd /data/whereami/math/Public-V2X-Datasets
export TMPDIR=/data/whereami/math/tools/tmp
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 PYTHONDONTWRITEBYTECODE=1
/data/whereami/math/tools/gdown/bin/python -u collection_261026/collect.py
