Documentation
=============
This area contains most of the functions that you will have to use. More information on individualized (and private)
functions can be found by looking through the codebase. Notably, the entire DRAGONDisplay class should only be used in this
app format, so there should be no need to use any of those methods individually.

DRAGON
------
.. autoclass:: dragon_inference.inference.DRAGONModel
.. autofunction:: dragon_inference.inference.DRAGONModel.predict

.. autoclass:: dragon_inference.inference.DRAGON

.. autoclass:: dragon_inference.inference.DRAGONEnsemble
.. autoclass:: dragon_inference.inference.DRAGONEnsemble.run_election

MCMC
----
.. autoclass:: dragon_inference.galaxy_inference.GalaxyInference
.. autofunction:: dragon_inference.galaxy_inference.GalaxyInference.init_params
.. autofunction:: dragon_inference.galaxy_inference.GalaxyInference.load_data
.. autofunction:: dragon_inference.galaxy_inference.GalaxyInference.get_contour_levels
.. autofunction:: dragon_inference.galaxy_inference.GalaxyInference.fit_radial_light_profile

HSC Downloader
--------------
This is provided in case you want an easy-to-use, simple interface for downloading
single image cutouts from HSC querying using an SDSS name.

.. autoclass:: dragon_inference.hsc_downloader.HSCDownloader
.. autofunction:: dragon_inference.hsc_downloader.HSCDownloader.cutout_query_sdss
.. autofunction:: dragon_inference.hsc_downloader.HSCDownloader.cutout_query_ra_dec
.. autofunction:: dragon_inference.hsc_downloader.HSCDownloader.download_spectrum
.. autofunction:: dragon_inference.hsc_downloader.HSCDownloader.query_spectrum

Miscellaneous
-------------
.. autofunction:: dragon_inference.utils.load_fits
.. autofunction:: dragon_inference.utils.get_fits_image
.. autofunction:: dragon_inference.utils.implot
.. autofunction:: dragon_inference.utils.discover_devices
.. autofunction:: dragon_inference.utils.arsinh_normalize
