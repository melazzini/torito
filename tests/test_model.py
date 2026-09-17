"""
Tests for TORITO. Those that evaluate the model need the grid file (see the README) and
are skipped without it. Run with:  pytest
"""

import numpy as np
import pytest

import torito
from torito.grid import NATIVE_EDGES, NATIVE_ENERGIES, grid_path
from torito.trusted import trusted_region_issues, usable_nh_range

needs_grid = pytest.mark.skipif(not grid_path().exists(), reason="TORITO grid not found")

PARS = dict(alpha=70.0, nh=3.0, nha=4.5, nav=4.0, afe=1.2)


def test_usable_nh_range_interpolates_between_nodes():
    assert usable_nh_range(2.0) == (0.50, 3.98)
    assert usable_nh_range(2.33)[1] == pytest.approx(4.749, abs=1e-3)
    assert usable_nh_range(0.5) == usable_nh_range(1.0)
    assert usable_nh_range(12.0) == usable_nh_range(10.0)


def test_trusted_region_issues():
    assert trusted_region_issues(nh=3.0, nha=4.5, nav=4.0) == []
    assert len(trusted_region_issues(nh=9.0, nha=1.5, nav=4.0)) == 1      # photon-starved
    assert len(trusted_region_issues(nh=3.0, nha=6.0, nav=12.0)) == 1     # nav off diagonal
    assert trusted_region_issues(nh=6.0, nha=6.0, nav=12.0) == []         # on the diagonal


@pytest.fixture(scope="module")
def model():
    from torito.sherpa_model import TorusModel
    m = TorusModel()
    for name, value in PARS.items():
        getattr(m, name).val = value
    return m


def values(model):
    return [p.val for p in model.pars]


@needs_grid
def test_native_bins_return_the_grid(model):
    native = torito.native_spectrum(**PARS)
    binned = model.calc(values(model), NATIVE_EDGES[:-1], NATIVE_EDGES[1:])
    point = model.calc(values(model), NATIVE_ENERGIES)
    assert native.shape == (1300,) and native.sum() > 0
    np.testing.assert_allclose(binned, native, rtol=1e-10)
    np.testing.assert_allclose(point, native, rtol=1e-10)


@needs_grid
def test_any_binning_conserves_photons(model):
    rng = np.random.default_rng(1)
    edges = np.sort(np.concatenate(([0.05, 400.0], rng.uniform(0.05, 400.0, 777))))
    total = model.calc(values(model), edges[:-1], edges[1:]).sum()
    assert total == pytest.approx(torito.native_spectrum(**PARS).sum(), rel=1e-10)


@needs_grid
def test_redshift_moves_the_iron_line(model):
    edges = np.linspace(3.0, 8.0, 5001)
    centres = 0.5 * (edges[:-1] + edges[1:])
    for z in (0.0, 0.5):
        p = values(model)
        p[-1] = z
        peak = centres[np.argmax(model.calc(p, edges[:-1], edges[1:]))]
        assert peak == pytest.approx(6.4 / (1 + z), abs=0.02)
