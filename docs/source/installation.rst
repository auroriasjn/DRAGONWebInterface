Installation
============

Getting started
---------------
Installation of this web interface should be relatively straightforward provided
that you have Anaconda installed. Anaconda is a **prerequisite** for getitng the entire
project to work and is **necessary** for running any of the DRAGON models without much pain.

This repository can be downloaded by running the following short command:

.. code-block:: console

   (.venv) $ git clone https://github.com/auroriasjn/DRAGONWebInterface.git

.. warning::

    Since there are 7 separate DRAGON models located in this repository, this
    will take a memory footprint of approximately **193 MB** of space. Do make sure
    that you have this available.

Upon installation, please **change directories** into the :file:`DRAGONWebInterface` directory:

.. code-block:: console

   (.venv) $ cd DRAGONWebInterface

.. note::

    If you have run the :file:`git clone` command exactly, this command should work fine. Otherwise,
    navigate to where you cloned the repository into and *then* run this command.

There are two *executables* located in the directory: :file:`install.sh` and :file:`run.sh`. Please
run these commands in that exact order:

.. code-block:: console

   (.venv) $ ./install.sh
   (.venv) $ ./run.sh

This will create a *new Conda environment* for you under the name **DRAGONInference**.

Manual Installation
-------------------
Alternatively, if you do not wish to use the automated commands, you can run the following suite. After
creating your *own* Anaconda environment with **Python 3.12 installed**, execute the following commands:

.. code-block:: console

   (.venv) $ pip install -r requirements.txt
   (.venv) $ pip install (-e) .

where the optional :file:`-e` flag indicates an editable build installation. The code can be directly run using

.. code-block:: console

   (.venv) $ streamlit run dragon_inference/frontend/frontend.py

This will create a **Streamlit** *local* web interface for convenience.
