import numpy as np
from typing import Tuple

import pytest


# Assuming the bbox function is defined as above
def bbox(data: np.ndarray) -> Tuple[slice, slice, slice]:
    """
    Compute the max bounding box of a 3D mask. It finds the smallest bounding
    box that encloses all non-zero elements in the given mask array.
    """
    non_zero_coords = np.argwhere(data)
    
    if non_zero_coords.size == 0:
        return (slice(0, 0), slice(0, 0), slice(0, 0))
    
    x_min, y_min, z_min = non_zero_coords.min(axis=0)
    x_max, y_max, z_max = non_zero_coords.max(axis=0) + 1

    return (slice(x_min, x_max), slice(y_min, y_max), slice(z_min, z_max))
