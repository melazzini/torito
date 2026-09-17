"""
TORITO: an interpolation model of the X-ray spectra of AGN obscured by a clumpy,
Compton-thick torus (Melazzini & Sazonov).

    import torito
    torito.load_grid("path/to/torito_grid_v1.npz")   # optional, see torito.grid

    from sherpa.astro import ui
    from torito.sherpa_model import TorusModel
    ui.add_model(TorusModel)                          # model type "torusmodel"
    src = ui.create_model_component("torusmodel", "src")
"""

from .grid import (NATIVE_EDGES, NATIVE_ENERGIES, alpha_deg_to_code, load_grid,
                   native_spectrum)
from .trusted import trusted_region_issues, usable_nh_range

__version__ = "0.1.0"
