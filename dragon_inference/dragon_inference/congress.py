import pandas as pd
import numpy as np
from collections import Counter
import logging
import os

from .model import DRAGONModel

class DRAGONEnsemble:
    def __init__(self, model_dir):
        """
        This is a helper class that helps to initialize our hard voting
        ensemble of DRAGON models by only specifying the model directory.

        :param model_dir: A string representing a directory which should contain
        .pt files of all of the DRAGON models the client wishes to use to make
        their prediction.
        """
        if not os.path.isdir(model_dir):
            raise RuntimeError("Invalid model directory specified.")

        # Extract only the model paths
        self.model_paths = [f"{model_dir}/{path}" for path in os.listdir(model_dir) if path.endswith('.pt')]
        self.model_dict = dict()

        # Register voterss
        self._register_voters()

    def _register_voters(self):
        logging.info(f"Registering voters...")
        for model_path in self.model_paths:
            self.model_dict[model_path] = DRAGONModel(model_path=model_path)

    def run_election(self, image):
        """
        Outside of the funny naming convention, running the election
        is equivalent to a hard voting system. We adapted this from
        classical machine learning theory and applied it to have
        a stronger confidence bound on our dual AGN candidates.

        :param image: a NumPy ndarray that contains the image data
        of the FITS file previously downloaded.
        :return: The Congressional aggregate data as a dictionary.
        """
        logging.info("Beginning election...")

        records = []
        for key, model in self.model_dict.items():
            pred_label, pred_conf, second_pred_label, second_pred_conf = model.predict(datum=image)

            # These are numpy arrays, so extract scalar values
            records.append({
                "voter": key,
                "pred_class": int(pred_label[0]),
                "pred_conf": float(pred_conf[0]),
                "second_pred_class": int(second_pred_label[0]),
                "second_pred_conf": float(second_pred_conf[0])
            })

        total_predictions = pd.DataFrame(records)

        # Running the ensemble phase.
        return self._certify_congress(total_predictions)

    def _certify_congress(self, total_predictions):
        """
        The Certify Congress method was originally created for the
        DRAGON module, but relied upon a formatting suitable
        for batch prediction. This time, we only need to certify for
        one example. Notably, this means that we do not include an
        optimism score.

        :param total_predictions: A DataFrame that contains the predictions of
        the congressional DRAGON models on a singular image.
        :return: The Congressional Aggregate in the form of a dictionary.
        """
        logging.info("Certifying Congressional results...")

        # Number of voters
        num_voters = len(self.model_dict)
        labels = pd.unique(
            pd.concat([
                total_predictions["pred_class"],
                total_predictions["second_pred_class"]
            ])
        )

        # Ensure labels are integers (in case of numpy objects)
        labels = [int(label) for label in labels]

        # First round: count votes and store confidences
        voter_vals = Counter()
        confidences = {label: [] for label in labels}

        logging.info("Aggregating counts and confidences...")
        for _, row in total_predictions.iterrows():
            voted_class = int(row['pred_class'])
            confidence = float(row['pred_conf'])
            voter_vals[voted_class] += 1
            confidences[voted_class].append(confidence)

        if not voter_vals:
            logging.warning("No votes were cast.")
            return {
                "voted_class": -1,
                "num_voters": 0,
                "total_voters": num_voters,
                "average_confidence": 0.0,
            }

        # Second round: check for close call / tie
        majority, maj_count = voter_vals.most_common(1)[0]
        voted_class = majority

        if len(voter_vals) > 1:
            second, second_count = voter_vals.most_common(2)[1]
            if (maj_count - 1) <= second_count <= maj_count:
                logging.info("Too close to call — tie detected.")
                voted_class = -1

        # Avoid division by zero
        if voted_class != -1 and confidences[voted_class]:
            avg_confidence = sum(confidences[voted_class]) / len(confidences[voted_class])
        else:
            avg_confidence = 0.0

        logging.info("Congressional voting completed...")
        output = {
            "voted_class": voted_class,
            "num_voters": maj_count if voted_class != -1 else 0,
            "total_voters": num_voters,
            "average_confidence": avg_confidence,
        }

        return output