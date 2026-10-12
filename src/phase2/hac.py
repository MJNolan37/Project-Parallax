"""
Project Parallax — Phase 2 hac.py
Heteroskedasticity and Autocorrelation Consistent (HAC) covariance estimators.

Specification: v1.0 Sections 3 (H1 HAC) and 7 (H2 multivariate HAC).

Two distinct HAC estimators:

H1 — Scalar Andrews QS-HAC with VAR(1) prewhitening
    Applied segment-wise to the scalar z_t residuals.
    Frozen recipe: Andrews quadratic-spectral kernel + automatic AR(1)-based
    bandwidth + VAR(1) prewhitening.
    Validated against R sandwich to 4 significant figures.

H2 — Score-based multivariate QS-HAC WITHOUT prewhitening
    Applied to the stacked G'×1 (one-break) or 2G'×1 (two-break) score vectors.
    No VAR(1) prewhitening: G=12 VAR(1) requires 144 parameters from T≈180.
    Bandwidth: B_T = max(1, max_g B_{T,g}) using per-sector Andrews AR(1) scalars.
    If segment has < 3 usable observations for AR(1) → assign bandwidth 1.
    Missing sectors → zero score contribution (handled in h2_system.py).

References:
    Andrews (1991) "Heteroskedasticity and Autocorrelation Consistent
        Covariance Matrix Estimation", Econometrica 59(3), 817–858.
    The QS kernel formula and bandwidth constants follow Andrews (1991) exactly.
    Prewhitening correction follows Andrews & Monahan (1992).
"""

from __future__ import annotations

import warnings
from typing import Optional

import numpy as np


# ---------------------------------------------------------------------------
# QS Kernel
# ---------------------------------------------------------------------------

def qs_kernel(x: float | np.ndarray) -> float | np.ndarray:
    """
    Quadratic Spectral (QS) kernel of Andrews (1991).

        k(x) = 25 / (12 π² x²) × [sin(6πx/5)/(6πx/5) − cos(6πx/5)]

    with k(0) = 1.

    Parameters
    ----------
    x : scalar or array of bandwidth-normalised lags h/m.

    Returns
    -------
    k : QS kernel weights; scalar or array matching input shape.
    """
    scalar_in = np.isscalar(x)
    x = np.atleast_1d(np.asarray(x, dtype=float))
    out = np.ones_like(x)

    nonzero = x != 0.0
    xnz = x[nonzero]
    arg = 6.0 * np.pi * xnz / 5.0
    out[nonzero] = (25.0 / (12.0 * np.pi**2 * xnz**2)) * (
        np.sin(arg) / arg - np.cos(arg)
    )
    return float(out[0]) if scalar_in else out


# ---------------------------------------------------------------------------
# Andrews (1991) AR(1)-based bandwidth selector — scalar
# ---------------------------------------------------------------------------

def _fit_ar1(u: np.ndarray) -> tuple[float, float]:
    """
    OLS fit of AR(1) without intercept: u_t = ρ u_{t-1} + e_t.

    Returns
    -------
    (rho_hat, sigma2_hat) : AR(1) coefficient and residual variance.
    """
    T = len(u)
    if T < 3:
        return 0.0, float(np.var(u)) if T > 0 else 1.0
    y = u[1:]
    x = u[:-1]
    rho_hat = float(np.dot(x, y) / np.dot(x, x))
    # Clamp to stationary region to avoid degenerate bandwidths
    rho_hat = np.clip(rho_hat, -0.9999, 0.9999)
    resid = y - rho_hat * x
    sigma2_hat = float(np.dot(resid, resid) / (T - 1))
    return rho_hat, sigma2_hat


def _qs_bandwidth_ar1(rho_hat: float, T: int) -> float:
    """
    Andrews (1991) optimal QS bandwidth via AR(1) approximation.

    For QS kernel with AR(1) process u_t = ρ u_{t-1} + e_t:
        α̂(2) = 4ρ̂² / (1 − ρ̂)⁴    [Andrews 1991, eq. 6.2–6.4, scalar case]
        m* = max(1, 1.3221 × (α̂(2) × T)^{1/5})

    Parameters
    ----------
    rho_hat : AR(1) coefficient (must satisfy |ρ| < 1).
    T       : sample length (usable observations in segment).

    Returns
    -------
    m : bandwidth (float ≥ 1).
    """
    if abs(rho_hat) < 1e-10:
        # White-noise process → minimum bandwidth
        return 1.0
    alpha2 = 4.0 * rho_hat**2 / (1.0 - rho_hat)**4
    m = 1.3221 * (alpha2 * T) ** 0.2
    return max(1.0, m)


# ---------------------------------------------------------------------------
# H1: Scalar long-run variance with VAR(1) prewhitening
# ---------------------------------------------------------------------------

def scalar_hac_prewhitened(u: np.ndarray) -> float:
    """
    Andrews (1991) / Andrews & Monahan (1992) scalar long-run variance estimator.

    Steps:
      1. Fit AR(1) to u: ρ̂, ê_t = u_t − ρ̂ u_{t-1}
      2. Select bandwidth m using α̂(2) from the AR(1) fit
      3. Compute kernel-weighted autocovariance Ŝ_ε of residuals ê_t
      4. Apply prewhitening correction: Ŝ_u = Ŝ_ε / (1 − ρ̂)²

    Parameters
    ----------
    u : 1-D array, demeaned segment residuals (length T_seg ≥ 3).

    Returns
    -------
    S_hat : estimated long-run variance (scalar ≥ 0).

    Notes
    -----
    If T_seg < 3, returns sample variance (no autocovariance structure estimable).
    This is the frozen H1 HAC recipe (v1.0 Section 3); do not alter.
    """
    u = np.asarray(u, dtype=float).ravel()
    T = len(u)
    if T < 3:
        return float(np.var(u)) if T > 0 else 0.0

    # Step 1: AR(1) prewhitening
    rho_hat, sigma2_hat = _fit_ar1(u)
    resid = u[1:] - rho_hat * u[:-1]  # length T-1

    # Step 2: Bandwidth from AR(1) coefficients
    m = _qs_bandwidth_ar1(rho_hat, T - 1)

    # Step 3: QS HAC on prewhitened residuals
    S_eps = _kernel_hac_scalar(resid, m)

    # Step 4: Prewhitening correction
    S_u = S_eps / (1.0 - rho_hat) ** 2
    return float(S_u)


def _kernel_hac_scalar(e: np.ndarray, m: float) -> float:
    """
    Kernel-weighted HAC estimator of the long-run variance for a scalar series.

        Ŝ = Σ_{h=-(T-1)}^{T-1} k(h/m) Γ̂(h)

    where Γ̂(h) = T⁻¹ Σ_{t=h+1}^T e_t e_{t-h}  (uncentred; mean assumed 0).
    """
    e = np.asarray(e, dtype=float).ravel()
    T = len(e)
    if T == 0:
        return 0.0
    # h=0 term
    S = np.dot(e, e) / T
    # h > 0 terms (symmetric, so multiply by 2)
    for h in range(1, T):
        w = qs_kernel(h / m)
        if abs(w) < 1e-14:
            break  # QS kernel decays; truncate
        gamma_h = np.dot(e[h:], e[:-h]) / T
        S += 2.0 * w * gamma_h
    return float(S)


# ---------------------------------------------------------------------------
# H2: Multivariate score-based QS-HAC (no prewhitening)
# ---------------------------------------------------------------------------

def multivariate_hac_scores(
    V: np.ndarray,
    bandwidth: Optional[float] = None,
    per_column_bandwidths: Optional[np.ndarray] = None,
) -> np.ndarray:
    """
    Score-based multivariate QS-HAC covariance estimator (H2, v1.0 Section 7).

    No VAR(1) prewhitening. Literal implementation of the v1.0 §7 formula:

        Γ̂(h) = Σ_{t=h+1}^{T} v_t v_{t-h}'    (no division by T)
        Σ̂ = k(0)·Γ̂(0) + Σ_{h=1}^{T-1} k(h/B_T)·[Γ̂(h) + Γ̂(h)']

    Segment-count normalisation is already embedded in the score construction
    (v_{g,t} = ε̂_{g,t} / T_{g,seg}), so no extra T factor is required here.
    The calling function run_h2 uses Sigma_hat directly without rescaling.

    Bandwidth B_T = max(1, max_g B_{T,g}) is computed externally from per-sector
    AR(1) estimates and passed in; alternatively pass `per_column_bandwidths`
    to have this function compute max internally.

    Parameters
    ----------
    V : array of shape (T, G') — score vectors; NaN entries must already be
        replaced with 0 by the caller (v1.0 §7 "missing → 0" rule).
    bandwidth : float ≥ 1, pre-computed B_T = max_g B_{T,g}. Either this or
        per_column_bandwidths must be provided.
    per_column_bandwidths : array of shape (G',) — per-sector scalar bandwidths;
        B_T = max of these (≥ 1). If provided, overrides bandwidth.

    Returns
    -------
    Sigma_hat : (G', G') symmetric positive semi-definite HAC matrix.

    Raises
    ------
    ValueError if neither bandwidth nor per_column_bandwidths is given.
    """
    V = np.asarray(V, dtype=float)
    T, G = V.shape

    # Resolve bandwidth
    if per_column_bandwidths is not None:
        bandwidth = float(max(1.0, np.max(per_column_bandwidths)))
    elif bandwidth is not None:
        bandwidth = float(max(1.0, bandwidth))
    else:
        raise ValueError(
            "Either bandwidth or per_column_bandwidths must be provided."
        )

    m = bandwidth
    Sigma = np.zeros((G, G))

    # h=0 term (Gamma(0)) — literal v1.0 §7: no division by T
    Sigma += V.T @ V

    # h=1,...,T-1 terms (symmetrised) — literal v1.0 §7: no division by T
    for h in range(1, T):
        w = qs_kernel(h / m)
        if abs(w) < 1e-14:
            break
        Gamma_h = V[h:].T @ V[:-h]   # (G, G)
        Sigma += w * (Gamma_h + Gamma_h.T)

    # Enforce symmetry numerically
    Sigma = 0.5 * (Sigma + Sigma.T)
    return Sigma


def per_sector_bandwidth(
    scores_g: np.ndarray,
    obs_mask: np.ndarray,
    min_obs_for_ar1: int = 3,
) -> float:
    """
    Compute the Andrews QS bandwidth for a single sector's scalar score series.

    v1.0 Section 7: "If a segment has fewer than 3 usable observations for
    AR(1) estimation, assign that coordinate bandwidth 1."

    Parameters
    ----------
    scores_g : 1-D array of length T.  Calendar-indexed; zeros at positions
               where obs_mask is False (structurally missing sector-months).
               Valid observations with score == 0.0 are included in the AR(1)
               pilot because they are distinguished by obs_mask.
    obs_mask : 1-D boolean array of length T.  obs_mask[t] = True means sector
               had a valid observation at month t (i.e., valid_mask[t, g]).
               Must be provided; inferring observability from score != 0.0 is
               unsafe because valid scores can equal zero (ε̂_{g,t} = 0 when
               an observation falls exactly on its segment mean).
    min_obs_for_ar1 : minimum observed entries to attempt AR(1) estimation.
                      If n_observed < min_obs_for_ar1, returns 1.0 (frozen
                      fallback per v1.0 §7).

    Returns
    -------
    b : float ≥ 1.

    Notes
    -----
    The sample size n_j = n_observed (number of True entries in obs_mask) is
    used as the T argument of the Andrews bandwidth formula.  This follows
    methods-review adjudication: use the genuinely observed count, not full
    calendar T, not post-prewhitening residual count.
    The final HAC (multivariate_hac_scores) still uses the full calendar-
    indexed zero-filled matrix with calendar lags.
    """
    scores_g = np.asarray(scores_g, dtype=float).ravel()
    obs_mask = np.asarray(obs_mask, dtype=bool).ravel()
    usable = scores_g[obs_mask]
    n_observed = len(usable)
    if n_observed < min_obs_for_ar1:
        return 1.0
    rho_hat, _ = _fit_ar1(usable)
    return _qs_bandwidth_ar1(rho_hat, n_observed)


def compute_h2_bandwidth(
    V: np.ndarray,
    valid_mask: np.ndarray,
    min_obs_for_ar1: int = 3,
) -> float:
    """
    Compute B_T = max(1, max_g B_{T,g}) across all G' sector columns.

    Parameters
    ----------
    V : (T, G') score matrix with zeros in place of missing values (calendar-
        indexed, zero-filled per v1.0 §7 "missing → 0" rule).
    valid_mask : (T, G') boolean array aligned with V's columns.
                 valid_mask[t, g] = True means sector g had a valid observation
                 at calendar month t.  Passed through to per_sector_bandwidth
                 as obs_mask for each column; must not be inferred from V.
    min_obs_for_ar1 : passed to per_sector_bandwidth.

    Returns
    -------
    B_T : float ≥ 1.
    """
    G = V.shape[1]
    bws = np.array([
        per_sector_bandwidth(V[:, g], valid_mask[:, g], min_obs_for_ar1)
        for g in range(G)
    ])
    return float(max(1.0, np.max(bws)))
