Usage
==========

Streamlit
---------------

The DRAGON Web App is a *localized Streamlit web interface* that allows direct user interaction with the DRAGON models. Effectively, the web app serves as a wrapper for the functionality of the DRAGON CNN, in addition to an auxiliary Markov Chain Monte Carlo (MCMC) method for predicting the Sersic light profile of a galaxy.

.. caution::

   The DRAGON Web App requires access to a **Hyper-Suprime Cam Wide Survey** account for downloading data. There **is no file upload option** (although future
   versions may contain this).

   If you need access to such an account, please visit `The HSC Data Access Page <https://hsc-release.mtk.nao.ac.jp/doc/index.php/data-access__pdr3/>`_ to create an account.

.. tip::

   Since this is a localized web app, you need not worry about security when inputting your credentials, as we guarantee that this
   program is only stored on your local machine.

The Streamlit App contains roughly 4 separate *pages* that can only be accessed sequentially:

#. **Login**: Here, your HSC credentials are required.
#. **Cutout Requester**: Here, you have an *automated interface* for downloading HSC data only by using an SDSS name.
#. **Viewer**: Here, you select whether or not you wish to conduct analysis with the **DRAGON** model or to use an **MCMC** fit.

   * **DRAGON** analysis comes in two parts:
      #. *Centroid Selection*: In Moskowitz and Ng et al. (in preparation), we use a GOTHIC profile fit and a Moffat2D light profile fit to select the centroids of our images. Here, you can manually select them instead.
      #. *Classification*: This will **run the PyTorch backend** and run inference with seven DRAGON models on your images, and calculate separation and magnitude using Aperture Photometry.
   * **Galaxy MCMC** will just run a backend MCMC method.

.. caution::

   The SDSS names can only be accepted in J2000 naming convention.

Manual
------

If you prefer to do your analysis in a Jupyter notebook or in a separate Python script, the DRAGON Interface package contains all of this information. For example,
to use our Congress Ensemble Package, you can use the following convenience moethods:

.. code-block:: python

   from dragon_inference.utils import load_fits
   from dragon_inference.inference import DRAGONEnsemble

   # Acquire data and initialize an ensemble learner.
   header, data = load_fits(file_path='<dummy path>')
   ensemble = DRAGONEnsemble(model_dir='models')

   # Extract predictions.
   preds = ensemble.run_election(image=data)

The :file:`DRAGONModel` class is used for initialization of the DRAGON models, yes; however, it can also dual function
as a general purpose PyTorch CNN wrapper, assuming that the outputs are in the form of a **labeled softmax one-hot encoded array**:

.. code-block:: python

   from dragon_inference.inference import DRAGONModel

   # Load some data
   header, data = load_fits(file_path='<dummy path>')

   # Initialize model and run prediction
   model = DRAGONModel(model_path='<model_path>')
   model.predict(datum=data)


Similarly, the Galaxy MCMC class can be initialized similarly.

.. code-block:: python

   from dragon_inference.galaxy_inference import GalaxyInference

   # Load some data
   header, data = load_fits(file_path='<dummy path>')

   # Initialize an MCMC model with given initial starting parameters.
   galaxy_mcmc = GalaxyInference(n_steps=10000, n_walkers=20)

   # Initialize params. These are bogus values.
   galaxy_mcmc.init_params(n=1, r_eff=10, i0=8, theta=0, ellip=0.5)

   # Run MCMC
   outputs = galaxy_mcmc.fit_radial_light_profile()

For more information, please see the :ref:`documentation` section.
