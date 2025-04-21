[![Documentation Status](https://readthedocs.org/projects/gampen/badge/?version=latest)](https://gampen.readthedocs.io/en/latest/?badge=latest)
[![Python Version 3.12](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/downloads/)
[![GitHub license](https://img.shields.io/github/license/auroriasjn/DRAGONWebInterface)](https://github.com/auroriasjn/DRAGONWebInterface/blob/master/LICENSE)
[![image](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

# DRAGON Web Interface
This repository serves as a convenient **web interface** for use in preliminary analysis of DRAGON candidates. For details on the model, please go to the [DRAGON_CNN](https://github.com/iam37/DRAGON_CNN/tree/main) repository. 

We intend for the DRAGON Dual AGN candidates to be an unstructured *public collaboration*. We have made all of the data on these candidates
(RA, Dec, J2000 objID, and even preliminary redshifts) available to be claimed. 

# Installation
Please ```git clone``` this repository by running the following command:
```angular2html
git clone https://github.com/auroriasjn/DRAGONWebInterface.git
```
Do be warned that since there are 7 separate DRAGON models, this will take up a memory footprint of approximately 193 MB.

Upon installation, please **change directories** into the `dragon_inference` directory:
```angular2html
cd DRAGONWebInterface/dragon_inference
```
Make sure that you have **Anaconda** installed. There are two files located in the folder: `install.sh` and `run.sh`. Please run `install.sh` first and then `run.sh`, where a convenience command is located below.
```angular2html
./install.sh && ./run.sh
```
This will open up a *localized Streamlit App*, probably on https://localhost:8501. Please check the terminal for the location of the hosted website. This will also create
an entirely new Anaconda environment for you called ```DRAGONInference```.

Do note that startup for the website will take a decent amount of time (on the order of 1 minute).

# Getting Help

If you have a question, please send me an e-mail either to `isaac.moskowitz@yale.edu` or
`jeremy.ng@yale.edu`. This package specifically was developed by `jeremy.ng@yale.edu`.





