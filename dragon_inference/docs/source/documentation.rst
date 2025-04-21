Documentation
=============
This area contains most of the functions that you will have to use. More information on individualized (and private)
functions can be found by looking through the codebase. Notably, the entire DRAGONDisplay class should only be used in this
app format, so there should be no need to use any of those methods individually.

DRAGON
------
.. autoclass:: dragon_inference.DRAGONModel
.. autofunction:: dragon_inference.DRAGONModel.predict

.. autoclass:: dragon_inference.DRAGONEnsemble
.. autoclass:: dragon_inference.DRAGONEnsemble.run_election

MCMC
----
.. autoclass:: galaxy_inference.GalaxyInference
.. autofunction:: galaxy_inference.GalaxyInference.init_params
.. autofunction:: galaxy_inference.GalaxyInference.load_data
.. autofunction:: galaxy_inference.GalaxyInference.get_contour_levels
.. autofunction:: galaxy_inference.GalaxyInference.fit_radial_light_profile
