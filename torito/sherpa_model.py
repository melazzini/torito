"""
TORITO as a Sherpa model, for any energy binning and redshift.

Sherpa evaluates a source model on the energy grid of the instrument response (RMF/ARF),
and the model must return the photons falling in each of those bins. The grid values are
photons per native bin, so a binned evaluation redistributes them without any bin-width
factor:

    edges_k = native bin edges, k = 0..1300
    G_k     = model value in native bin k
    C(E)    = cumulative photons below E:  C(edges_0) = 0,  C(edges_k+1) = C(edges_k) + G_k,
              linear in E inside each native bin

    for each requested bin [lo, hi] (observed frame, keV):
        lo', hi' = lo*(1+z), hi*(1+z)                     # rest frame
        photons  = norm * (C(hi') - C(lo')) / (1+z)       # 1/(1+z): time dilation

C is constant outside 0.1-300 keV, so bins beyond the grid get no photons and bins that
straddle an end get only the covered part. The total number of photons is conserved for
any binning, requesting exactly the native bins returns exactly G, and narrow features
such as the Fe K-alpha line keep their photons. With a free `norm`, the 1/(1+z) factor
only changes what `norm` means.

When Sherpa passes energies without bin edges (a plain Data1D), the model returns the
grid shape interpolated at those energies.

Parameters:

    norm      overall normalization (arbitrary units), >= 0
    alpha     viewing angle, DEGREES, 60.1-79.9
    nh        line-of-sight column density, 10^24 cm^-2, 0.501-9.9
    nha       average torus column density, 10^24 cm^-2, 1.0-9.9
    nav       average number of clouds along the line of sight, 2-15.9
                (above 8, only on the N_H = <N_H> diagonal; see torito.trusted)
    afe       iron abundance relative to solar (Feldman 1992), 0.501-1.99
    redshift  source redshift, frozen at 0 by default

The interpolation is piecewise linear and not smooth across grid-node planes, so a global
optimizer such as Sherpa's `moncar` is safer than a local one.
"""

import numpy as np

from sherpa.models.model import RegriddableModel1D
from sherpa.models.parameter import Parameter

from .grid import E_MAX_KEV, E_MIN_KEV, NATIVE_EDGES, NATIVE_ENERGIES, native_spectrum


def photons_in_bins(native, lo, hi, redshift=0.0):
    """Photons in the observed-frame bins [lo, hi] (keV), from the native-bin values."""
    cumulative = np.concatenate(([0.0], np.cumsum(native)))
    shift = 1.0 + redshift
    upper = np.interp(np.asarray(hi, dtype=float) * shift, NATIVE_EDGES, cumulative)
    lower = np.interp(np.asarray(lo, dtype=float) * shift, NATIVE_EDGES, cumulative)
    return (upper - lower) / shift


def shape_at(native, energies, redshift=0.0):
    """Model shape at point energies (keV, observed frame): the unbinned fallback."""
    rest = np.asarray(energies, dtype=float) * (1.0 + redshift)
    inside = (rest >= E_MIN_KEV) & (rest <= E_MAX_KEV)
    out = np.zeros_like(rest)
    out[inside] = np.interp(np.log(rest[inside]), np.log(NATIVE_ENERGIES), native)
    return out


class TorusModel(RegriddableModel1D):
    """TORITO: clumpy Compton-thick torus X-ray spectrum, any binning, any redshift."""

    def __init__(self, name="torito"):
        self.norm = Parameter(name, "norm", 1.0, min=0.0, max=1e10, hard_min=0.0)
        self.alpha = Parameter(name, "alpha", 70.0, min=60.1, max=79.9,
                               hard_min=60.1, hard_max=79.9, units="deg")
        self.nh = Parameter(name, "nh", 3.0, min=0.501, max=9.9,
                            hard_min=0.501, hard_max=9.9, units="1e24 cm^-2")
        self.nha = Parameter(name, "nha", 3.0, min=1.0, max=9.9,
                             hard_min=1.0, hard_max=9.9, units="1e24 cm^-2")
        self.nav = Parameter(name, "nav", 4.0, min=2.0, max=15.9,
                             hard_min=2.0, hard_max=15.9)
        self.afe = Parameter(name, "afe", 1.0, min=0.501, max=1.99,
                             hard_min=0.501, hard_max=1.99)
        self.redshift = Parameter(name, "redshift", 0.0, min=0.0, max=10.0,
                                  hard_min=0.0, frozen=True)
        super().__init__(name, (self.norm, self.alpha, self.nh, self.nha, self.nav,
                                self.afe, self.redshift))

    def calc(self, p, lo, hi=None, *args, **kwargs):
        norm, alpha, nh, nha, nav, afe, z = p
        native = native_spectrum(alpha, nh, nha, nav, afe)
        if hi is None:
            return norm * shape_at(native, lo, z)
        return norm * photons_in_bins(native, lo, hi, z)
