import logging
from astropy.modeling import models
import emcee
import corner
import numpy as np

from multiprocessing import Pool


# Mostly just a wrapper for astropy https://petrofit.readthedocs.io/en/latest/fitting_workflow.html
class GalaxyInference:
    def __init__(self, n_steps, n_walkers):
        """
        Initialize the GalaxyInference class.
        :param n_steps: Number of production steps in the MCMC chain.
        :param n_walkers: Number of walkers in the ensemble.
        """
        logging.info("Initializing Galaxy MCMC Inference...")
        self.n_steps = n_steps
        self.n_walkers = n_walkers

    def init_params(self,
                    n: float,
                    r_eff: float,
                    i0: float,
                    theta: int,
                    ellip: float,
                    sz: int = 94):
        # Initializing parameters for MCMC
        self.n = n
        self.r_eff = r_eff
        self.i0 = i0
        self.theta = theta
        self.ellip = ellip

        # Assume that the initial guess for the center is right at the center of the image
        self.x0, self.y0 = sz // 2, sz // 2

    def load_data(self, image):
        """
        Simple setter method to load data into the MCMC pipeline.
        :param image: a numpy.ndarray that contains the image data.
        """
        logging.info("Data loaded...")
        self.data = image

    def _curve_model(self, params):
        logging.debug("New model instantiated!")
        n, r_eff, i0, theta, ellip, x0, y0 = params

        sersic_model = models.Sersic2D(
            amplitude=i0,
            r_eff=r_eff,
            n=n,
            x_0=x0,
            y_0=y0,
            ellip=ellip,
            theta=theta
        )

        yy, xx = np.indices(self.data.shape)
        model_image = sersic_model(xx, yy)
        return model_image

    def _lnprior(self, params):
        # A log prior is necessary for EMCEE to work.
        n, r_eff, i0, theta, ellip, x0, y0 = params

        # Sersic index between 0.5 and 8
        if not (0.5 < n < 8.0):
            return -np.inf

        # Effective radius positive and no longer than the image itself.
        if not (0 < r_eff < self.data.shape[0]):
            return -np.inf

        # Intensity (amplitude) must be positive.
        if i0 <= 0:
            return -np.inf

        # Theta is an angle in radians; here we constrain it between 0 and 2π.
        if not (0 <= theta < 2 * np.pi):
            return -np.inf

        # Ellipticity between 0 (circular) and 1 (highly elongated).
        if not (0 <= ellip < 1):
            return -np.inf

        # Center coordinate
        if not (0 <= x0 <= self.data.shape[0]) or (0 <= y0 <= self.data.shape[1]):
            return -np.inf

        # Otherwise, assume a uniform prior.
        return 0.0

    def _lnprob(self, params, data):
        lp = self._lnprior(params)
        if not np.isfinite(lp):
            return -np.inf
        return lp + self._lnlike(params, data)

    def _lnlike(self, params, data):
        model_image = self._curve_model(params)
        sigma2 = np.std(data) ** 2
        lnlike = -0.5 * np.sum(((data - model_image) ** 2) / sigma2 + np.log(2 * np.pi * sigma2))
        return lnlike

    def _run_mcmc(self):
        # Initial parameters loaded from init_params
        initial = np.array([self.n, self.r_eff, self.i0, self.theta, self.ellip, self.x0, self.y0])
        n_dim = len(initial)
        N_BURNIN = int(self.n_steps * 0.05)

        # Create initial walker positions by adding a small random perturbation to the initial guess.
        # Define parameter-specific scales (adjust the scales based on your parameter ranges)
        scale = np.array([0.5, 0.5, 10.0, 0.1, 0.01, 0.5, 0.5])
        p0 = initial + scale * np.random.randn(self.n_walkers, n_dim)

        cov_matrix = np.cov(p0, rowvar=False)
        condition_number = np.linalg.cond(cov_matrix)
        logging.info("Initial condition number:", condition_number)

        with Pool() as pool:
            logging.info("Beginning MCMC... initial parameters initialized.")
            sampler = emcee.EnsembleSampler(
                self.n_walkers, n_dim, self._lnprob, args=(self.data,), pool=pool
            )

            logging.info("Running burn-in...")
            p0, _, _ = sampler.run_mcmc(p0, N_BURNIN, progress=True, skip_initial_state_check=True)
            logging.info("Burn-in Complete...")

            sampler.reset()

            logging.info("Running production...")
            pos, prob, state = sampler.run_mcmc(p0, self.n_steps, progress=True, skip_initial_state_check=True)

        return pos, prob, state, sampler

    def get_contour_levels(self, params, n_levels=8):
        """
        Helper method to get the contour plots.
        """
        model = self._curve_model(params)

        # Plot the levels
        levels = np.linspace(np.percentile(model, 5),
                             np.percentile(model, 95),
                             n_levels)

        return model, levels

    def fit_radial_light_profile(self):
        """
        This method actually runs inference to determine
        a galaxy's radial light profile in terms of its
        Sersic index (following a generalized Sersic law).
        :return: The final working state of the MCMC model, and a
        corner plot that represents its results (pos, prob, state, sample, figure).
        """
        logging.info("Beginning fitting...")
        pos, prob, state, sampler = self._run_mcmc()

        # Discard the burn-in samples.
        flat_samples = sampler.get_chain(discard=100, thin=10, flat=True)

        figure = corner.corner(
            flat_samples,
            labels=["$n$", "$R_e$", "$I_0$", "$\\theta$", "$\\epsilon$", "$x_0$", "$y_0$"],
            show_titles=True,
            title_kwargs={"fontsize": 12}
        )

        param_names = ["n", "R_e", "I_0", "\\theta", "\\epsilon", "x_0", "y_0"]
        inferred_params = {}

        # Getting corner plot outputs in the form of a dictionary.
        for i, name in enumerate(param_names):
            q16, q50, q84 = np.percentile(flat_samples[:, i], [16, 50, 84])
            inferred_params[name] = {
                "median": q50,
                "minus_1sigma": q50 - q16,
                "plus_1sigma": q84 - q50
            }

        return pos, prob, state, sampler, figure, inferred_params