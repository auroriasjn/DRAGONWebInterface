import torch

def arsinh_normalize(X):
    """Normalize a Torch tensor with arsinh."""
    normalized = torch.log(X + (X ** 2 + 1) ** 0.5)
    normalized[torch.isnan(normalized)] = 0  # Replace NaN values with 0
    normalized[torch.isinf(normalized)] = 255
    return normalized
