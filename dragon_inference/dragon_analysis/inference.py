from dragon_inference import DRAGONEnsemble
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

    # Only to be run if there are two sources
    def detect_centroids(self):
        pass

    # Separation and Magnitude calculation, previously
    # done by Isaac and I over the summer, but
    # definitely requires some fine-tuning to look nice
    def calculate_separations(self):
        pass

    def calculate_magnitudes(self):
        pass