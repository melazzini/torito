"""
Where the TORITO grid can be trusted (Section 2.4 of the paper).

Two restrictions apply inside the fitted parameter ranges:

1. Photon statistics. For each average torus column density <N_H> of the grid, only a
   range of line-of-sight columns N_H is covered by simulations with enough photons
   (at least 1000 per spectrum). Between two <N_H> nodes, both bounds are interpolated
   linearly; outside the tabulated nodes, the nearest node's bounds apply.

2. Cloud number. The clumpy simulations have <N_c> = 2, 3, 4, 5 and 8; the smooth torus
   enters the grid as <N_c> = 16, but only on the N_H = <N_H> diagonal. Away from that
   diagonal, <N_c> > 8 is an extrapolation.

The fit does not enforce these restrictions: checking a result against them is up to the
user, with `trusted_region_issues`.
"""

import numpy as np

# Usable N_H range (10^24 cm^-2) at each <N_H> node (10^24 cm^-2).
NHA_NODE_NH_BOUNDS = {
    1:  (0.50, 2.51),
    2:  (0.50, 3.98),
    3:  (0.50, 6.31),
    4:  (0.50, 7.94),
    5:  (0.50, 10.00),
    6:  (0.63, 10.00),
    8:  (1.00, 10.00),
    10: (1.58, 10.00),
}
NHA_NODES = sorted(NHA_NODE_NH_BOUNDS)
NAV_CLUMPY_MAX = 8.0           # largest simulated cloud number
DIAGONAL_TOLERANCE_DEX = 0.05  # half a grid step in N_H: "on the N_H = <N_H> diagonal"


def usable_nh_range(nha):
    """Usable line-of-sight N_H range (10^24 cm^-2) for an average torus column nha."""
    if nha <= NHA_NODES[0]:
        return NHA_NODE_NH_BOUNDS[NHA_NODES[0]]
    if nha >= NHA_NODES[-1]:
        return NHA_NODE_NH_BOUNDS[NHA_NODES[-1]]
    for lo_node, hi_node in zip(NHA_NODES[:-1], NHA_NODES[1:]):
        if lo_node <= nha <= hi_node:
            lo_bounds = NHA_NODE_NH_BOUNDS[lo_node]
            hi_bounds = NHA_NODE_NH_BOUNDS[hi_node]
            w = (nha - lo_node) / (hi_node - lo_node)
            return (lo_bounds[0] + w * (hi_bounds[0] - lo_bounds[0]),
                    lo_bounds[1] + w * (hi_bounds[1] - lo_bounds[1]))


def trusted_region_issues(nh, nha, nav):
    """
    Reasons why (nh, nha, nav) lies outside the region where the grid can be trusted;
    an empty list means none. "On the diagonal" is taken as within
    DIAGONAL_TOLERANCE_DEX of N_H = <N_H>, an approximate convention.
    """
    issues = []
    lo, hi = usable_nh_range(nha)
    if not lo <= nh <= hi:
        issues.append(f"N_H = {nh:.3g} is outside the usable range {lo:.3g}-{hi:.3g} "
                      f"(1e24 cm^-2) for <N_H> = {nha:.3g}")
    if nav > NAV_CLUMPY_MAX and abs(np.log10(nh / nha)) > DIAGONAL_TOLERANCE_DEX:
        issues.append(f"<N_c> = {nav:.3g} > {NAV_CLUMPY_MAX:g} is only supported where "
                      f"N_H = <N_H>, but N_H = {nh:.3g} and <N_H> = {nha:.3g}")
    return issues
