#! /bin/bash

set -euo pipefail

if ! command -v conda &>/dev/null; then
  echo "ERROR: conda not found. Please install Miniconda/Anaconda first." >&2
  exit 1
fi

conda create -n "DRAGONInference" python=3.12

source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate DRAGONInference
pip install -r requirements.txt
pip install .
