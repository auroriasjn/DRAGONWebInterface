#! /bin/bash

# Activating the CONDA environment
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate DRAGONInference

streamlit run dragon_inference/frontend/frontend.py