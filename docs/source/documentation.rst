Documentation
=============
This area contains most of the functions that you will have to use. More information on individualized (and private)
functions can be found by looking through the codebase. Notably, the entire DRAGONDisplay class should only be used in this
app format, so there should be no need to use any of those methods individually.

DRAGON
------
.. autoclass:: dragon_inference.inference.DRAGONModel
.. autoclass:: dragon_inference.inference.DRAGON
.. autoclass:: dragon_inference.inference.DRAGONEnsemble

MCMC
----
.. autoclass:: dragon_inference.galaxy_inference.GalaxyInference

HSC Downloader
--------------
This is provided in case you want an easy-to-use, simple interface for downloading
single image cutouts from HSC querying using an SDSS name.

.. autoclass:: dragon_inference.hsc_downloader.HSCDownloader

Miscellaneous
-------------
.. autofunction:: dragon_inference.utils.load_fits
.. autofunction:: dragon_inference.utils.get_fits_image
.. autofunction:: dragon_inference.utils.implot
.. autofunction:: dragon_inference.utils.discover_devices
.. autofunction:: dragon_inference.utils.arsinh_normalize
