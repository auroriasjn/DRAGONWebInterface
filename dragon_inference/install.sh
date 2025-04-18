#! /bin/bash

conda create -n "DRAGONInference" python=3.12
conda activate DRAGONInference
pip install -r requirements.txt
pip install .
