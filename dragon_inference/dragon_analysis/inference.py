from dragon_inference import DRAGONEnsemble
from photutils import CircularAperture, CircularAnnulus, aperture_photometry
from .centroid_point import CentroidPoint
from typing import List

import numpy as np
import logging

class DRAGONAnalysis:
    def __init__(self, model_dir='models'):
        """
        Interface to run DRAGON.
        """
        logging.info("Initializing DRAGON models...")
        self.ensemble = DRAGONEnsemble(model_dir=model_dir)

    def run(self, image):
        # Using the ensemble!
        classification = self.ensemble.run_election(image=image)
        return classification

    @staticmethod
    def calculate_magnitudes(
            image: np.ndarray,
            center_coords: List[CentroidPoint],
            radii: List[float],
            fluxmag_0: float
    ):
        """
        This is an adaptation of Isaac's magnitude calculation code done over the summer
        in conjunction with me!

        :param image:
        :param center_coords:
        :param radii:
        :return:
        """
        adu_mag_conv = lambda flux, fluxMag_0: 2.5 * np.log10(fluxMag_0 / flux)

        logging.info("Calculating magnitudes...")
        aperture_1 = CircularAperture(center_coords[0], r=radii[0])
        aperture_2 = CircularAperture(center_coords[1], r=radii[1])

        phot_table_1 = aperture_photometry(image, aperture_1)
        phot_table_2 = aperture_photometry(image, aperture_2)

        # Trusting Isaac here with this part
        for col1, col2 in zip(phot_table_1.colnames, phot_table_2.colnames):
            phot_table_1[col1].info.format = '%.8g'
            phot_table_2[col2].info.format = '%.8g'

        adu1 = phot_table_1['aperture_sum'].value[0]
        adu2 = phot_table_2['aperture_sum'].value[0]

        inst_mag_1 = adu_mag_conv(adu1, fluxmag_0)
        inst_mag_2 = adu_mag_conv(adu2, fluxmag_0)

        flux_ratio = 10 ** (-(inst_mag_1 - inst_mag_2) / 2.5)
        if flux_ratio < 1:  # to consistently compare the brighter quasar to the dimmer quasar in the pair
            flux_ratio = 1 / flux_ratio

        mag_difference = np.abs(inst_mag_1 - inst_mag_2)

        # Final output as a dictionary
        return {
            "magnitude_1": inst_mag_1,
            "magnitude_2": inst_mag_2,
            "flux_ratio": flux_ratio,
            "diff": mag_difference,
            "aperture1": aperture_1,
            "aperture2": aperture_2
        }

    @staticmethod
    def angular_separation(ra1, dec1, ra2, dec2):
        ra1 = np.radians(ra1)
        dec1 = np.radians(dec1)
        ra2 = np.radians(ra2)
        dec2 = np.radians(dec2)

        delta_ra = ra2 - ra1
        delta_dec = dec2 - dec1

        c = 2 * np.arcsin(
            np.sqrt(np.sin(delta_dec / 2) ** 2 +
                    np.cos(dec1) * np.cos(dec2) * (np.sin(delta_ra / 2) ** 2))
        )  # Haversine formula.

        return np.degrees(c)

    @staticmethod
    def separation(p1: CentroidPoint, p2: CentroidPoint):
        if p1.ra is None or p2.ra is None:
            raise RuntimeError("P1 and P2 must have an associated RA and Dec.")

        return DRAGONAnalysis.angular_separation(ra1=p1.ra, ra2=p2.ra, dec1=p1.dec, dec2=p2.dec)