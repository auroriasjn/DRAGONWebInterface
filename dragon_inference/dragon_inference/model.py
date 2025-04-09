import torch
import torch.nn as nn
import numpy as np
import logging
from utils import discover_devices, arsinh_normalize

from .cnn import DRAGON

class DRAGONModel:
    def __init__(self, model_path):
        """
        A helper method to initialize a DRAGON model. Basically just a glorified PyTorch
        model interface.

        :param model_path: The location of the model to load. All of them are the same anyways!
        """
        logging.info(f"The model here is located at {model_path}.")
        self.model_path = model_path

        # Initialize the model
        self.model = DRAGON()

        self.device = discover_devices()
        self.model = nn.DataParallel(self.model)
        self.model = self.model.to(self.device)

        logging.info(f"Loading state dict...")
        if self.device == 'cpu':
            self.model.load_state_dict(torch.load(model_path, map_location='cpu'))
        else:
            self.model.load_state_dict(torch.load(model_path))

    def predict(self, datum: np.ndarray):
        """
        Predict a label for a single image.
        :param datum: A single grayscale image of shape [192, 192] as a numpy array.
        """
        logging.info("Prediction...")
        self.model.eval()

        # Convert numpy array to PyTorch tensor
        datum = torch.from_numpy(datum).float()  # ensure float type
        datum = arsinh_normalize(datum)

        # Reshape: [H, W] -> [1, 1, H, W] (Batch x Channel x Height x Width)
        datum = datum.unsqueeze(0).unsqueeze(0)

        with torch.no_grad():
            datum = datum.to(self.device)
            outputs = self.model(datum)
            outputs = nn.functional.softmax(outputs, dim=1)

        values, indices = torch.topk(outputs, 2, dim=1)

        predicted_confs, predicted_labels = torch.max(outputs, 1)
        second_predicted_confs = values[:, 1]
        second_predicted_labels = indices[:, 1]

        return (predicted_labels.cpu().numpy(),
                predicted_confs.cpu().numpy(),
                second_predicted_labels.cpu().numpy(),
                second_predicted_confs.cpu().numpy())

