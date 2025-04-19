#! /bin/bash

# Activating the CONDA environment
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate DRAGONInference

streamlit run frontend/frontend.py