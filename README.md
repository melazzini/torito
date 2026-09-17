# TORITO

TORITO (Spanish for "little torus") is an interpolation model of the X-ray spectra of active
galactic nuclei obscured by a clumpy, Compton-thick torus. It is built on a grid of Monte
Carlo simulations of X-ray reprocessing and returns the full emergent spectrum, from 0.1 to
300 keV: the transmitted continuum, the Compton-scattered emission and the fluorescent
lines, all computed for the same clumpy medium.

The model is described in *Interpolation Model For Fitting AGN X-Ray Spectra*
(F. Melazzini and S. Sazonov, in preparation).

## Parameters

| Parameter | Meaning | Range |
| --- | --- | --- |
| $\alpha$ | viewing angle, measured from the torus axis | 60°–80° |
| $N_\mathrm{H}$ | line-of-sight column density | $0.5$–$10\times10^{24}\,\mathrm{cm^{-2}}$ |
| $\langle N_\mathrm{H}\rangle$ | average torus column density | $1$–$10\times10^{24}\,\mathrm{cm^{-2}}$ |
| $\langle N_\mathrm{c}\rangle$ | average number of clouds along the line of sight | 2–8, plus the smooth-torus limit |
| $A_\mathrm{Fe}$ | iron abundance relative to solar | 0.5–2 |

plus a free normalization. The primary continuum is fixed, with photon index
$\Gamma=1.8$ and cutoff energy $E_\mathrm{cut}=300$ keV, and so is the half-opening angle
of the torus, $\theta=60°$.

The grid cannot be trusted everywhere inside these ranges: at some combinations of the two
column densities the simulations have too few photons, and $\langle N_\mathrm{c}\rangle>8$
is only supported where $N_\mathrm{H}=\langle N_\mathrm{H}\rangle$. See Section 2.4 of the
paper.

## Installation

```bash
git clone https://github.com/melazzini/torito.git
cd torito
pip install .
```

TORITO needs NumPy, SciPy and [Sherpa](https://sherpa.readthedocs.io).

The model also needs the interpolation grid, `torito_grid_v1.npz` (about 50 MB), which is
distributed separately, on Zenodo:
[doi:10.5281/zenodo.22819418](https://doi.org/10.5281/zenodo.22819418).

```bash
mkdir -p ~/.torito
curl -L -o ~/.torito/torito_grid_v1.npz https://zenodo.org/records/22819419/files/torito_grid_v1.npz
```

TORITO looks for the file in this order:

1. the path given to `torito.load_grid(path)`;
2. the `TORITO_GRID` environment variable;
3. `~/.torito/torito_grid_v1.npz`.

## Usage with Sherpa

```python
from sherpa.astro import ui
import torito
from torito.sherpa_model import TorusModel

ui.add_model(TorusModel)                    # registers the model type "torusmodel"
ui.load_pha("source.pha")                   # with its RMF, ARF and background
src = ui.create_model_component("torusmodel", "src")
ui.set_source(src)                          # add Galactic absorption etc. as needed
src.redshift = 0.0165

ui.set_stat("cstat")
ui.set_method("moncar")                     # the model is not smooth: prefer a global optimizer
ui.fit()

print(torito.trusted_region_issues(src.nh.val, src.nha.val, src.nav.val))
```

The first evaluation builds the interpolator, which takes about a minute.

- **Any binning and redshift.** The model returns the number of photons in each energy
  bin Sherpa asks for, conserving their total, so it can be folded through the response of
  any X-ray instrument.
- **Units.** The grid spectra are photons per logarithmic bin times an arbitrary constant,
  absorbed by `norm`. `alpha` is in degrees, `nh` and `nha` in $10^{24}\,\mathrm{cm^{-2}}$.
- **Trusted region.** The fit does not enforce the restrictions described above;
  `torito.trusted_region_issues` checks a result against them.
- **Components.** TORITO describes the torus and the obscured nucleus only. Other
  components of a real spectrum, such as Galactic absorption or a scattered power law, are
  added as usual.

Run the tests with `pytest` (those that evaluate the model are skipped without the grid).

## Status

Coming soon:

- more tutorials on fitting observed spectra;
- an XSPEC table model.

## Documentation

- [Fitting with Sherpa](notebooks/sherpa_example.ipynb): a step-by-step example, from
  creating the model to fitting a simulated NuSTAR-like spectrum, checking the result and
  estimating uncertainties.
- [Sensitivity maps](docs/sensitivity_maps.md): how strongly each part of the spectrum
  responds to each parameter across the grid.

## Citation

Please cite the paper, and the grid as
[doi:10.5281/zenodo.22819418](https://doi.org/10.5281/zenodo.22819418).

## License

The code is MIT, see [LICENSE](LICENSE). The interpolation grid is distributed under
CC BY 4.0.
