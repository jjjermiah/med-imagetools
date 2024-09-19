from mitk.utils.bbox import bbox
import numpy as np

# 10 tests for the bbox function

def test_empty_array():
    """Test with an empty array (all zeros)."""
    data = np.zeros((5, 5, 5), dtype=int)
    assert bbox(data) == (slice(0, 0), slice(0, 0), slice(0, 0))

def test_filled_array():
    """Test with a fully filled array (all ones)."""
    data = np.ones((5, 5, 5), dtype=int)
    assert bbox(data) == (slice(0, 5), slice(0, 5), slice(0, 5))

def test_single_point():
    """Test with a single non-zero point."""
    data = np.zeros((5, 5, 5), dtype=int)
    data[2, 2, 2] = 1
    assert bbox(data) == (slice(2, 3), slice(2, 3), slice(2, 3))

def test_non_zero_block():
    """Test with a small non-zero block in the array."""
    data = np.zeros((10, 10, 10), dtype=int)
    data[2:4, 3:5, 4:6] = 1
    assert bbox(data) == (slice(2, 4), slice(3, 5), slice(4, 6))

def test_edge_non_zero():
    """Test with non-zero elements touching the edges of the array."""
    data = np.zeros((10, 10, 10), dtype=int)
    data[0, 0, 0] = 1
    data[9, 9, 9] = 1
    assert bbox(data) == (slice(0, 10), slice(0, 10), slice(0, 10))

def test_zero_shape_array():
    """Test with an array of shape (0, 0, 0)."""
    data = np.zeros((0, 0, 0), dtype=int)
    assert bbox(data) == (slice(0, 0), slice(0, 0), slice(0, 0))

def test_line_along_x_axis():
    """Test with a line of non-zero values along the x-axis."""
    data = np.zeros((5, 5, 5), dtype=int)
    data[:, 2, 2] = 1
    assert bbox(data) == (slice(0, 5), slice(2, 3), slice(2, 3))

def test_line_along_y_axis():
    """Test with a line of non-zero values along the y-axis."""
    data = np.zeros((5, 5, 5), dtype=int)
    data[2, :, 2] = 1
    assert bbox(data) == (slice(2, 3), slice(0, 5), slice(2, 3))

def test_line_along_z_axis():
    """Test with a line of non-zero values along the z-axis."""
    data = np.zeros((5, 5, 5), dtype=int)
    data[2, 2, :] = 1
    assert bbox(data) == (slice(2, 3), slice(2, 3), slice(0, 5))

def test_multiple_blocks():
    """Test with two disjoint blocks of non-zero values."""
    data = np.zeros((10, 10, 10), dtype=int)
    data[1:3, 1:3, 1:3] = 1
    data[7:9, 7:9, 7:9] = 1
    assert bbox(data) == (slice(1, 9), slice(1, 9), slice(1, 9))

