"""
The TORITO interpolation grid: loading it and evaluating the model on its native bins.

The grid file (torito_grid_v1.npz) holds the Monte Carlo spectra and their parameters:

    points    (N, 5)     alpha_code, nh, nha, nav, afe
    spectra   (N, 1300)  photons per native logarithmic bin, times one arbitrary constant
    edges     (1301,)    native bin edges, keV (0.1-300 keV, logarithmic)

The spectra are not per keV: a value is the number of photons in its bin, i.e. it is
proportional to E dN/dE. The constant is absorbed by the model normalization.

The model is a piecewise-linear interpolation on the Delaunay triangulation of the points
(scipy's LinearNDInterpolator), returning 0 outside their convex hull. It is built on the
first evaluation, which takes about a minute, and kept for the rest of the session.

Where the grid file is looked for, in order: the path given to `load_grid`, the
TORITO_GRID environment variable, and ~/.torito/torito_grid_v1.npz.
"""

import os
from pathlib import Path

import numpy as np
from scipy.interpolate import LinearNDInterpolator

GRID_FILE_NAME = "torito_grid_v1.npz"
DEFAULT_GRID_PATH = Path.home() / ".torito" / GRID_FILE_NAME

# The viewing angle enters the grid as a band code: 0 -> 60-70 deg, 1 -> 70-80, 2 -> 80-90.
ALPHA_DEG_AT_CODE_0 = 60.0
ALPHA_DEG_PER_CODE = 10.0

E_MIN_KEV, E_MAX_KEV, N_BINS = 0.1, 300.0, 1300
NATIVE_EDGES = E_MIN_KEV * (E_MAX_KEV / E_MIN_KEV) ** (np.arange(N_BINS + 1) / N_BINS)
NATIVE_ENERGIES = 0.5 * (NATIVE_EDGES[:-1] + NATIVE_EDGES[1:])   # tabulated midpoints

_interpolator = None


def alpha_deg_to_code(alpha_deg):
    return (alpha_deg - ALPHA_DEG_AT_CODE_0) / ALPHA_DEG_PER_CODE


def grid_path(path=None):
    """The grid file to use (see the module docstring)."""
    if path is not None:
        return Path(path).expanduser()
    if os.environ.get("TORITO_GRID"):
        return Path(os.environ["TORITO_GRID"]).expanduser()
    return DEFAULT_GRID_PATH


def load_grid(path=None):
    """
    Build the interpolator from the grid file and keep it for later evaluations.
    Calling it again replaces the grid in use.
    """
    global _interpolator
    path = grid_path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"TORITO grid not found at {path}. Download {GRID_FILE_NAME} (see the README) "
            f"and pass its path to torito.load_grid(), set TORITO_GRID, or place it at "
            f"{DEFAULT_GRID_PATH}.")
    with np.load(path) as grid:
        points, spectra = grid["points"], grid["spectra"]
        if not np.allclose(grid["edges"], NATIVE_EDGES):
            raise ValueError(f"{path}: unexpected energy grid")
    _interpolator = LinearNDInterpolator(points, spectra, fill_value=0)
    return _interpolator


def native_spectrum(alpha, nh, nha, nav, afe):
    """
    Model values in the 1300 native bins (photons per bin, arbitrary scale), >= 0.

    alpha      viewing angle, degrees
    nh, nha    line-of-sight and average torus column densities, 10^24 cm^-2
    nav        average number of clouds along the line of sight
    afe        iron abundance relative to solar
    """
    if _interpolator is None:
        load_grid()
    values = _interpolator(alpha_deg_to_code(alpha), nh, nha, nav, afe)
    return np.clip(np.asarray(values, dtype=float).ravel(), 0.0, None)
