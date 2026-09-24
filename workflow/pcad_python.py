"""Python translation of the MATLAB PCAD functions.

Translated from:
- PCAD_function.m
- BearingRate_prod.m
- d_dot_cal.m

Designed for use in Jupyter Notebook / Python pipelines.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Optional, Tuple

import numpy as np
from scipy.integrate import quad
from scipy.stats import norm


@dataclass
class PCADParams:
    # Gaussian parameters for subject and neighboring vehicles
    sigxs: float = 0.8
    sigys: float = 1.7
    sigxn: float = 4.28
    sigyn: float = 3.86

    # accumulation times
    tps: float = 0.13
    tpn: float = 0.01

    # weighting exponent
    alpha: float = 0.52

    # imaginary velocity restrictions
    fb: float = 30.0
    bb: float = -10.0
    lb: float = 6.0
    rb: float = -6.0

    # vehicle corner offsets used in the original MATLAB code
    # subject front-left/front-right: [4, +/-4]
    # neighbor rear-left/rear-right: [2, +/-1]
    subject_front_x: float = 4.0
    subject_half_width_for_bearing: float = 4.0
    neighbor_rear_x: float = 2.0
    neighbor_half_width_for_bearing: float = 1.0

    # grid search settings
    coarse_dvx: Tuple[float, float, float] = (-5.0, 0.0, 0.5)
    coarse_dvy: Tuple[float, float, float] = (-2.0, 2.0, 0.5)
    mid_radius: float = 0.5
    mid_step: float = 0.05
    fine_radius: float = 0.05
    fine_step: float = 0.01


def _safe_norm(vec: np.ndarray, eps: float = 1e-12) -> float:
    n = float(np.linalg.norm(vec))
    return max(n, eps)


def _arange_inclusive(start: float, stop: float, step: float) -> np.ndarray:
    """MATLAB-like inclusive range for floating grids."""
    if step <= 0:
        raise ValueError("step must be positive")
    n = int(math.floor((stop - start) / step + 1e-9))
    arr = start + step * np.arange(n + 1)
    if arr.size == 0 or arr[-1] < stop - step * 0.5:
        arr = np.append(arr, stop)
    return arr


def d_dot_cal(
    s_x: float, s_vx: float, s_y: float, s_vy: float,
    n_x: float, n_vx: float, n_y: float, n_vy: float,
) -> float:
    """Distance changing rate d_dot between subject and neighbor.

    d_dot < 0 means the two vehicles are getting closer.
    """
    pi = np.array([s_x, s_y], dtype=float)
    pj = np.array([n_x, n_y], dtype=float)
    vi = np.array([s_vx, s_vy], dtype=float)
    vj = np.array([n_vx, n_vy], dtype=float)
    d = _safe_norm(pi - pj)
    return float(np.dot(pi - pj, vi - vj) / d)


def bearing_rate_prod(
    omega: float,
    x_s: float, vx_s: float, y_s: float, vy_s: float,
    x_n: float, vx_n: float, y_n: float, vy_n: float,
    params: PCADParams = PCADParams(),
) -> float:
    """Python version of BearingRate_prod.m.

    It computes the product of the maximum and minimum bearing rates
    between selected corner points of subject and neighbor vehicles.
    Positive value is used by the original PCAD code as an avoidance criterion.
    """
    w = np.array([0.0, 0.0, omega], dtype=float)
    pj = np.array([x_n, y_n, 0.0], dtype=float)
    pi = np.array([x_s, y_s, 0.0], dtype=float)

    pi1 = pi + np.array([params.subject_front_x, params.subject_half_width_for_bearing, 0.0])
    pi2 = pi + np.array([params.subject_front_x, -params.subject_half_width_for_bearing, 0.0])
    pj3 = pj + np.array([params.neighbor_rear_x, params.neighbor_half_width_for_bearing, 0.0])
    pj4 = pj + np.array([params.neighbor_rear_x, -params.neighbor_half_width_for_bearing, 0.0])

    vi = np.array([vx_s, vy_s, 0.0], dtype=float)
    vi1 = vi + np.cross(pi1 - pi, w)
    vi2 = vi + np.cross(pi2 - pi, w)
    vj = np.array([vx_n, vy_n, 0.0], dtype=float)

    def theta(a: np.ndarray, vi_corner: np.ndarray) -> float:
        rel = a
        denom = _safe_norm(rel) ** 2
        val = (-np.cross(rel, vi_corner) + np.cross(rel, vj)) / denom
        return float(val[2])

    th1 = theta(pj3 - pi1, vi1)
    th2 = theta(pj4 - pi1, vi1)
    th3 = theta(pj3 - pi2, vi2)
    th4 = theta(pj4 - pi2, vi2)

    vals = np.array([th1, th2, th3, th4], dtype=float)
    return float(np.max(vals) * np.min(vals))


def _truncated_imaginary_speed_length(
    dx: float, dy: float, sigx: float, sigy: float, params: PCADParams,
) -> float:
    """Expected magnitude k of the imaginary velocity along the inter-vehicle direction.

    This corresponds to the integral-based block in MATLAB's PCAD_function.m.
    """
    dist = math.hypot(dx, dy)
    if dist < 1e-12:
        return 0.0

    ux = dx / dist
    uy = dy / dist
    ax = abs(dx) / dist
    ay = abs(dy) / dist

    denom_x = norm.cdf(params.fb / sigx) - norm.cdf(params.bb / sigx)
    denom_y = norm.cdf(params.lb / sigy) - norm.cdf(params.rb / sigy)
    if denom_x <= 0 or denom_y <= 0:
        return 0.0

    def density(k: float) -> float:
        comp_x = k * ux
        comp_y = k * uy
        if not (params.bb < comp_x < params.fb and params.rb < comp_y < params.lb):
            return 0.0
        px = (norm.pdf(k * ax / sigx) / sigx) / denom_x
        py = (norm.pdf(k * ay / sigy) / sigy) / denom_y
        return float(px * py)

    prob, _ = quad(density, 0.0, np.inf, limit=100)
    if prob <= 1e-15 or not np.isfinite(prob):
        return 0.0

    expected, _ = quad(lambda k: density(k) * k / prob, 0.0, np.inf, limit=100)
    if not np.isfinite(expected):
        return 0.0
    return float(expected)


def _search_min_delta_v(
    x_s: float, vx_s: float, y_s: float, vy_s: float,
    x_n: float, vx_n: float, y_n: float, vy_n: float,
    dvx_values: np.ndarray, dvy_values: np.ndarray,
    params: PCADParams,
    require_positive_norm: bool = False,
) -> Optional[Tuple[float, float, float]]:
    best = None
    best_len = math.inf
    for dvx in dvx_values:
        for dvy in dvy_values:
            if require_positive_norm and math.hypot(float(dvx), float(dvy)) <= 0:
                continue
            fm = bearing_rate_prod(
                0.0, x_s, vx_s + float(dvx), y_s, vy_s + float(dvy),
                x_n, vx_n, y_n, vy_n, params=params,
            )
            if fm > 0:
                vec_len = math.hypot(float(dvx), float(dvy))
                if vec_len < best_len:
                    best_len = vec_len
                    best = (float(dvx), float(dvy), float(vec_len))
    return best


def pcad_function(
    x_s: float, x_n: float, y_s: float, y_n: float,
    vx_s: float, vx_n: float, vy_s: float, vy_n: float,
    ax_s: float, ax_n: float, ay_s: float, ay_n: float,
    params: PCADParams = PCADParams(),
    return_details: bool = False,
):
    """Python translation of MATLAB PCAD_function.m.

    Parameters follow the MATLAB order:
    x_s, x_n, y_s, y_n, vx_s, vx_n, vy_s, vy_n, ax_s, ax_n, ay_s, ay_n

    Returns
    -------
    pcad : float
        Potential Collision Avoidance Difficulty.
    details : dict, optional
        Returned only when return_details=True.
    """
    values = [x_s, x_n, y_s, y_n, vx_s, vx_n, vy_s, vy_n, ax_s, ax_n, ay_s, ay_n]
    if any(v is None or not np.isfinite(float(v)) for v in values):
        return (np.nan, {}) if return_details else np.nan

    pi = np.array([x_s, y_s, 0.0], dtype=float)
    pj = np.array([x_n, y_n, 0.0], dtype=float)
    dist = _safe_norm(pj - pi)

    # Imaginary velocity for neighboring vehicle: direction from neighbor to subject.
    v_in_len = _truncated_imaginary_speed_length(
        dx=x_n - x_s, dy=y_n - y_s,
        sigx=params.sigxn, sigy=params.sigyn, params=params,
    )
    v_in = v_in_len * ((pi - pj) / dist)
    vx_n_adj = vx_n + v_in[0] + ax_n * params.tpn
    vy_n_adj = vy_n + v_in[1] + ay_n * params.tpn

    # Imaginary velocity for subject vehicle: direction from subject to neighbor.
    v_is_len = _truncated_imaginary_speed_length(
        dx=x_n - x_s, dy=y_n - y_s,
        sigx=params.sigxs, sigy=params.sigys, params=params,
    )
    v_is = -v_is_len * ((pi - pj) / dist)
    vx_s_adj = vx_s + v_is[0] + ax_s * params.tps
    vy_s_adj = vy_s + v_is[1] + ay_s * params.tps

    ddot = d_dot_cal(x_s, vx_s_adj, y_s, vy_s_adj, x_n, vx_n_adj, y_n, vy_n_adj)
    if ddot >= 0:
        details = {"d_dot": ddot, "delta_vx": 0.0, "delta_vy": 0.0, "v_s_adj": (vx_s_adj, vy_s_adj), "v_n_adj": (vx_n_adj, vy_n_adj)}
        return (0.0, details) if return_details else 0.0

    # 1) coarse search
    dvx = _arange_inclusive(*params.coarse_dvx)
    dvy = _arange_inclusive(*params.coarse_dvy)
    best = _search_min_delta_v(x_s, vx_s_adj, y_s, vy_s_adj, x_n, vx_n_adj, y_n, vy_n_adj, dvx, dvy, params)
    if best is None or (best[0] == 0.0 and best[1] == 0.0):
        details = {"d_dot": ddot, "delta_vx": 0.0, "delta_vy": 0.0, "v_s_adj": (vx_s_adj, vy_s_adj), "v_n_adj": (vx_n_adj, vy_n_adj)}
        return (0.0, details) if return_details else 0.0

    # 2) mid search around current best
    vx_best, vy_best, _ = best
    dvx = _arange_inclusive(vx_best - params.mid_radius, vx_best + params.mid_radius, params.mid_step)
    dvy = _arange_inclusive(vy_best - params.mid_radius, vy_best + params.mid_radius, params.mid_step)
    best_mid = _search_min_delta_v(x_s, vx_s_adj, y_s, vy_s_adj, x_n, vx_n_adj, y_n, vy_n_adj, dvx, dvy, params)
    if best_mid is not None:
        vx_best, vy_best, _ = best_mid

    # 3) fine search around current best
    dvx = _arange_inclusive(vx_best - params.fine_radius, vx_best + params.fine_radius, params.fine_step)
    dvy = _arange_inclusive(vy_best - params.fine_radius, vy_best + params.fine_radius, params.fine_step)
    best_fine = _search_min_delta_v(
        x_s, vx_s_adj, y_s, vy_s_adj, x_n, vx_n_adj, y_n, vy_n_adj,
        dvx, dvy, params, require_positive_norm=True,
    )
    vec_len = math.hypot(vx_best, vy_best) if best_fine is None else best_fine[2]
    if best_fine is not None:
        vx_best, vy_best = best_fine[0], best_fine[1]

    # Original MATLAB formula: PCAD = vec_len * (vx_s / 100 * 3.6)^alpha
    # Use adjusted vx_s to match the MATLAB code after velocity adjustment.
    speed_weight_base = vx_s_adj / 100.0 * 3.6
    if speed_weight_base < 0:
        # fractional alpha with negative base would be complex; clip for robustness.
        speed_weight_base = 0.0
    pcad = float(vec_len * (speed_weight_base ** params.alpha))

    details = {
        "d_dot": ddot,
        "delta_vx": vx_best,
        "delta_vy": vy_best,
        "delta_v_norm": vec_len,
        "v_s_adj": (vx_s_adj, vy_s_adj),
        "v_n_adj": (vx_n_adj, vy_n_adj),
        "v_In_len": v_in_len,
        "v_Is_len": v_is_len,
    }
    return (pcad, details) if return_details else pcad


def compute_pcad_for_pair_dataframe(
    df,
    prefix_s: str = "ego",
    prefix_n: str = "nbr",
    params: PCADParams = PCADParams(),
):
    """Convenience function for a DataFrame containing ego/neighbor state columns.

    Expected columns:
    {prefix}_x, {prefix}_y, {prefix}_vx, {prefix}_vy, {prefix}_ax, {prefix}_ay
    {prefix_n}_x, ...
    """
    out = []
    for _, r in df.iterrows():
        out.append(
            pcad_function(
                r[f"{prefix_s}_x"], r[f"{prefix_n}_x"],
                r[f"{prefix_s}_y"], r[f"{prefix_n}_y"],
                r[f"{prefix_s}_vx"], r[f"{prefix_n}_vx"],
                r[f"{prefix_s}_vy"], r[f"{prefix_n}_vy"],
                r[f"{prefix_s}_ax"], r[f"{prefix_n}_ax"],
                r[f"{prefix_s}_ay"], r[f"{prefix_n}_ay"],
                params=params,
            )
        )
    return np.asarray(out, dtype=float)
