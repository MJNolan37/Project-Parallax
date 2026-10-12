"""
Project Parallax — Phase 2 h2_system.py
H2 sector heterogeneity system: score construction and Wald test.

Specification: v1.0 Sections 6, 7, 8 (2026-09-23, frozen).

Design overview:
    H2 tests whether the change in FIRM share is homogeneous across FF12 sectors.
    Break dates are inherited from H1 — NOT re-estimated within H2.
    The Wald test uses a FULL estimated covariance matrix; no diagonal
    approximation; no fallback. v1.0 Section 8 singularity rule is strict.

Score construction (v1.0 Section 7):
    One-break (at t=τ₁, segments 1=[1,τ₁], 2=[τ₁+1,T]):
        v_{g,t} = −ε̂_{g,t} / T_{g,1}    t ∈ segment 1
        v_{g,t} = +ε̂_{g,t} / T_{g,2}    t ∈ segment 2
    Two-break (at t=τ₁, τ₂, segments 1=[1,τ₁], 2=[τ₁+1,τ₂], 3=[τ₂+1,T]):
        Episode 1 scores: (−1/T_{g,1}, +1/T_{g,2}, 0)
        Episode 2 scores: (0, −1/T_{g,2}, +1/T_{g,3})
        Stacked vector: [v_{g,t}^{(1)}, v_{g,t}^{(2)}]  (length 2G')
    Missing sector-months → 0 (not excluded).

Wald test (v1.0 Section 8):
    One-break: W = (RΔ̂)'(RΣ̂R')⁻¹(RΔ̂)  ~ χ²(G'−1)
    Two-break: W_joint  ~ χ²(2(G'−1))
    Contrast matrix R ∈ ℝ^{(G'−1)×G'}: rows = e_{j+1}' − e_1'
    R_joint = block_diag(R, R)

    Singularity rule (v1.0 Section 8, strict):
        M = RΣ̂R' (contracted covariance)
        κ(M) > 10⁸ → "H2 Wald test not computable"
        Report: condition number, full eigenvalue spectra of M and Σ̂,
                HAC bandwidth, non-missing sector-month counts.
        NO ridge/Tikhonov/diagonal approximation/bootstrap fallback.

Output codes:
    "ok"            : Wald statistic computed
    "not_computed"  : G' < 6 (insufficient sector coverage)
    "singular"      : κ(M) > 10⁸ (singularity rule triggered)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from .hac import multivariate_hac_scores, compute_h2_bandwidth

# Frozen constants (v1.0)
KAPPA_THRESHOLD: float = 1.0e8
G_MIN: int = 6
CV_CHI2_11: float = 19.68   # χ²(11) at 5%, one break G'=12
CV_CHI2_22: float = 33.92   # χ²(22) at 5%, two breaks G'=12
N_MIN: int = 5               # minimum stocks per sector-month


# ---------------------------------------------------------------------------
# Contrast matrix
# ---------------------------------------------------------------------------

def contrast_matrix(G_prime: int) -> np.ndarray:
    """
    Build R ∈ ℝ^{(G'−1)×G'}: rows = e_{j+1}' − e_1' for j=1,...,G'−1.

    Parameters
    ----------
    G_prime : number of qualifying sectors.

    Returns
    -------
    R : contrast matrix.
    """
    if G_prime < 2:
        raise ValueError(f"G' must be ≥ 2 to form contrast matrix; got {G_prime}")
    R = np.zeros((G_prime - 1, G_prime))
    R[:, 0] = -1.0
    for j in range(G_prime - 1):
        R[j, j + 1] = 1.0
    return R


def block_diag_R(R: np.ndarray) -> np.ndarray:
    """R_joint = block_diag(R, R) for two-break case."""
    d = R.shape[0]
    k = R.shape[1]
    R_joint = np.zeros((2 * d, 2 * k))
    R_joint[:d, :k] = R
    R_joint[d:, k:] = R
    return R_joint


# ---------------------------------------------------------------------------
# Score construction
# ---------------------------------------------------------------------------

def build_scores_one_break(
    residuals: np.ndarray,
    tau1: int,
    valid_mask: np.ndarray,
    G_prime_indices: list[int],
) -> np.ndarray:
    """
    Build G'×T score matrix for one-break case.

    Score formula (v1.0 §7):
        v_{g,t} = −ε̂_{g,t} / T_{g,1}    t ∈ [1, τ1]  (0-indexed: [0, τ1))
        v_{g,t} = +ε̂_{g,t} / T_{g,2}    t ∈ [τ1+1, T] (0-indexed: [τ1, T))
        Missing → 0

    Parameters
    ----------
    residuals : (T, G) array of within-sector OLS residuals ε̂_{g,t}.
                NaN where sector g is not observed at time t.
    tau1      : break date (1-indexed, inclusive end of segment 1).
                In 0-indexed Python: segment 1 = [0, tau1), segment 2 = [tau1, T).
    valid_mask : (T, G) boolean — True where sector g has N_min stocks.
    G_prime_indices : list of G' qualifying sector column indices.

    Returns
    -------
    V : (T, G') score matrix (columns = qualifying sectors).
    """
    T, G = residuals.shape
    G_prime = len(G_prime_indices)
    V = np.zeros((T, G_prime))

    for out_idx, g in enumerate(G_prime_indices):
        eps_g = np.where(valid_mask[:, g], residuals[:, g], np.nan)
        # Segment lengths (usable observations)
        T_g1 = int(np.sum(~np.isnan(eps_g[:tau1])))
        T_g2 = int(np.sum(~np.isnan(eps_g[tau1:])))
        # Scores
        for t in range(tau1):
            if not np.isnan(eps_g[t]) and T_g1 > 0:
                V[t, out_idx] = -eps_g[t] / T_g1
            # else: 0 (already initialised)
        for t in range(tau1, T):
            if not np.isnan(eps_g[t]) and T_g2 > 0:
                V[t, out_idx] = eps_g[t] / T_g2

    return V


def build_scores_two_break(
    residuals: np.ndarray,
    tau1: int,
    tau2: int,
    valid_mask: np.ndarray,
    G_prime_indices: list[int],
) -> np.ndarray:
    """
    Build 2G'×T stacked score matrix for two-break case.

    Episode 1: (−1/T_{g,1}, +1/T_{g,2}, 0)
    Episode 2: (0, −1/T_{g,2}, +1/T_{g,3})
    Stacked column order: [ep1_scores (G'), ep2_scores (G')]
    But returned as (T, 2G') matrix where columns are interleaved by episode.

    Note: shared middle segment enters BOTH episodes with opposite signs,
    so cross-episode covariance is captured directly within the HAC.

    Returns
    -------
    V_stack : (T, 2G') matrix — columns [ep1_col1,...,ep1_colG', ep2_col1,...,ep2_colG'].
    """
    T, G = residuals.shape
    G_prime = len(G_prime_indices)
    V1 = np.zeros((T, G_prime))  # episode 1
    V2 = np.zeros((T, G_prime))  # episode 2

    for out_idx, g in enumerate(G_prime_indices):
        eps_g = np.where(valid_mask[:, g], residuals[:, g], np.nan)
        # Segment usable obs
        T_g1 = int(np.sum(~np.isnan(eps_g[:tau1])))
        T_g2 = int(np.sum(~np.isnan(eps_g[tau1:tau2])))
        T_g3 = int(np.sum(~np.isnan(eps_g[tau2:])))

        # Episode 1 scores: seg1=−1/T_g1, seg2=+1/T_g2, seg3=0
        for t in range(tau1):
            if not np.isnan(eps_g[t]) and T_g1 > 0:
                V1[t, out_idx] = -eps_g[t] / T_g1
        for t in range(tau1, tau2):
            if not np.isnan(eps_g[t]) and T_g2 > 0:
                V1[t, out_idx] = eps_g[t] / T_g2
        # seg3: 0 for episode 1

        # Episode 2 scores: seg1=0, seg2=−1/T_g2, seg3=+1/T_g3
        for t in range(tau1, tau2):
            if not np.isnan(eps_g[t]) and T_g2 > 0:
                V2[t, out_idx] = -eps_g[t] / T_g2
        for t in range(tau2, T):
            if not np.isnan(eps_g[t]) and T_g3 > 0:
                V2[t, out_idx] = eps_g[t] / T_g3
        # seg1: 0 for episode 2

    return np.hstack([V1, V2])  # (T, 2G')


# ---------------------------------------------------------------------------
# Wald test
# ---------------------------------------------------------------------------

@dataclass
class WaldResult:
    status: str                      # "ok" | "not_computed" | "singular"
    n_breaks: int                    # 0, 1, or 2
    G_prime: int                     # number of qualifying sectors
    wald_stat: Optional[float] = None
    df: Optional[int] = None
    critical_value: Optional[float] = None
    reject_h0: Optional[bool] = None

    # Diagnostics (always populated)
    hac_bandwidth: Optional[float] = None
    kappa_M: Optional[float] = None
    eigenvalues_M: Optional[np.ndarray] = None
    eigenvalues_Sigma: Optional[np.ndarray] = None
    nonmissing_sector_month_counts: Optional[dict] = None
    cap_notes: list[str] = field(default_factory=list)


def _sector_shift_estimates(
    residuals: np.ndarray,
    tau1: int,
    tau2: Optional[int],
    valid_mask: np.ndarray,
    G_prime_indices: list[int],
) -> np.ndarray:
    """
    Compute segment mean differences Δ̂_g for each qualifying sector.

    One-break:  Δ̂_g = ȳ_{g,2} − ȳ_{g,1}
    Two-break:  Δ̂_g = (δ_{g,1}, δ_{g,2}) where
                δ_{g,j} = mean of segment j+1 − mean of segment j

    Returns Δ̂ as array of shape (G',) for one-break or (G', 2) for two-break.
    Note: for the Wald, we use the level means per segment, not residual means.
    The caller should pass the within-sector z series (not residuals after
    grand-mean removal) if testing level shifts directly.
    """
    G_prime = len(G_prime_indices)
    T = residuals.shape[0]

    if tau2 is None:
        # One-break
        delta = np.zeros(G_prime)
        for out_idx, g in enumerate(G_prime_indices):
            seg1 = residuals[:tau1, g]
            seg2 = residuals[tau1:, g]
            mask1 = valid_mask[:tau1, g]
            mask2 = valid_mask[tau1:, g]
            mu1 = np.nanmean(seg1[mask1]) if mask1.any() else 0.0
            mu2 = np.nanmean(seg2[mask2]) if mask2.any() else 0.0
            delta[out_idx] = mu2 - mu1
        return delta
    else:
        # Two-break: two episodes
        delta = np.zeros((G_prime, 2))
        for out_idx, g in enumerate(G_prime_indices):
            seg1 = residuals[:tau1, g]; mask1 = valid_mask[:tau1, g]
            seg2 = residuals[tau1:tau2, g]; mask2 = valid_mask[tau1:tau2, g]
            seg3 = residuals[tau2:, g]; mask3 = valid_mask[tau2:, g]
            mu1 = np.nanmean(seg1[mask1]) if mask1.any() else 0.0
            mu2 = np.nanmean(seg2[mask2]) if mask2.any() else 0.0
            mu3 = np.nanmean(seg3[mask3]) if mask3.any() else 0.0
            delta[out_idx, 0] = mu2 - mu1   # episode 1
            delta[out_idx, 1] = mu3 - mu2   # episode 2
        return delta


def wald_test(
    delta_hat: np.ndarray,
    Sigma_hat: np.ndarray,
    G_prime: int,
    n_breaks: int,
) -> WaldResult:
    """
    Compute H2 Wald test statistic (v1.0 Section 8).

    Parameters
    ----------
    delta_hat : (G',) for one-break or (2G',) for two-break.
                Stacked sector shift estimates.
    Sigma_hat : (G', G') or (2G', 2G') full HAC covariance matrix.
    G_prime   : number of qualifying sectors.
    n_breaks  : 1 or 2.

    Returns
    -------
    WaldResult with status, wald_stat, df, critical_value, reject_h0,
    kappa_M, eigenvalues_M, eigenvalues_Sigma.
    """
    if n_breaks == 1:
        R = contrast_matrix(G_prime)
        df = G_prime - 1
        cv = CV_CHI2_11 if G_prime == 12 else None
    elif n_breaks == 2:
        R = block_diag_R(contrast_matrix(G_prime))
        df = 2 * (G_prime - 1)
        cv = CV_CHI2_22 if G_prime == 12 else None
    else:
        raise ValueError(f"n_breaks must be 1 or 2; got {n_breaks}")

    # Contracted covariance M = R Σ̂ R'
    M = R @ Sigma_hat @ R.T
    M = 0.5 * (M + M.T)  # numerical symmetry

    eigs_Sigma = np.linalg.eigvalsh(Sigma_hat)
    eigs_M = np.linalg.eigvalsh(M)
    kappa_M = float(np.linalg.cond(M))

    result = WaldResult(
        status="ok",
        n_breaks=n_breaks,
        G_prime=G_prime,
        df=df,
        critical_value=cv,
        kappa_M=kappa_M,
        eigenvalues_M=eigs_M,
        eigenvalues_Sigma=eigs_Sigma,
    )

    # Singularity rule (v1.0 §8, strict)
    if kappa_M > KAPPA_THRESHOLD:
        result.status = "singular"
        return result

    # Compute Wald statistic
    RD = R @ delta_hat
    try:
        M_inv = np.linalg.inv(M)
    except np.linalg.LinAlgError:
        result.status = "singular"
        return result

    W = float(RD @ M_inv @ RD)
    result.wald_stat = W
    result.reject_h0 = (W > cv) if cv is not None else None
    return result


# ---------------------------------------------------------------------------
# High-level H2 entry point
# ---------------------------------------------------------------------------

@dataclass
class H2Result:
    status: str          # "ok" | "not_computed" | "singular"
    G_prime: int
    n_breaks: int
    wald: Optional[WaldResult] = None
    nonmissing_counts: Optional[dict] = None
    notes: list[str] = field(default_factory=list)


def run_h2(
    sector_z: np.ndarray,
    valid_mask: np.ndarray,
    break_dates: list[int],
    n_min: int = N_MIN,
    g_min: int = G_MIN,
) -> H2Result:
    """
    Run H2 sector heterogeneity test.

    Parameters
    ----------
    sector_z   : (T, G) array of within-sector z series (logit FIRM share per FF12).
                 NaN where sector has < N_min stocks.
    valid_mask : (T, G) boolean — True where sector-month qualifies (≥ N_min stocks).
    break_dates : list of 1 or 2 break dates from H1, 1-indexed, end-of-segment.
                  e.g. [tau1] or [tau1, tau2].
    n_min      : minimum stocks for sector-month validity.
    g_min      : minimum qualifying sectors; < g_min → not computed.

    Returns
    -------
    H2Result

    valid_mask Contract (v1.0 §§ 2, 5, 6)
    ----------------------------------------
    valid_mask[t, g] = True if and only if ALL of the following hold:
      1. Sector g has >= N_MIN (= 5) valid stocks in calendar month t.
      2. Each of those stocks has >= 10 valid daily return days in month t
         (the Option B data-quality filter applied during Phase 1 CLMX
         recomputation at the sector level).
    valid_mask[t, g] = False otherwise.  No partial counts: a sector-month
    is valid or missing, not fractionally valid.

    Where each rule is applied:
      10-day rule: applied at the individual-stock × month level in the empirical
          data pipeline (upstream of run_h2). Each stock either qualifies for the
          month or does not.
      N_min = 5 rule: applied at the sector × month level. After filtering stocks
          by the 10-day rule, count remaining stocks in sector g for month t.
          If count < N_MIN, set valid_mask[t, g] = False.

    How missing sector-months become zero score contributions:
      build_scores_one_break / build_scores_two_break iterate over (t, out_idx)
      pairs. When valid_mask[t, g] is False, the residual is NaN. The score
      assignment is conditional on non-NaN residuals: V[t, out_idx] remains 0.0
      for NaN residuals, implementing v1.0 §7 "missing → 0" rule.

    How sector eligibility across H1 segments is derived:
      A sector g qualifies for H2 if and only if valid_mask[s:e, g].any() is True
      for every H1 segment [s, e). Sectors missing an entire segment are excluded
      from G'. Break dates tau1 (and tau2 for two breaks) define segment boundaries;
      they come from H1 and are not re-estimated here.

    Caller responsibility:
      run_h2 does NOT apply the 10-day or N_min filters internally. It trusts
      valid_mask as the fully pre-filtered boolean index. The empirical pipeline
      must construct valid_mask correctly before calling run_h2; an incorrectly
      permissive valid_mask will silently pass ineligible sectors.
    """
    T, G = sector_z.shape
    n_breaks = len(break_dates)
    if n_breaks not in (1, 2):
        raise ValueError(f"H2 requires 1 or 2 break dates; got {n_breaks}")

    # Count qualifying sectors: have ≥ 1 valid observation in EVERY segment
    tau1 = break_dates[0]
    tau2 = break_dates[1] if n_breaks == 2 else None

    def segment_ranges(tau1, tau2, T):
        if tau2 is None:
            return [(0, tau1), (tau1, T)]
        return [(0, tau1), (tau1, tau2), (tau2, T)]

    segs = segment_ranges(tau1, tau2, T)

    qualifying = []
    nonmissing_counts = {}
    for g in range(G):
        qualifies_all_segs = all(
            valid_mask[s:e, g].any() for s, e in segs
        )
        if qualifies_all_segs:
            qualifying.append(g)
        total_valid = int(valid_mask[:, g].sum())
        nonmissing_counts[g] = total_valid

    G_prime = len(qualifying)

    if G_prime < g_min:
        return H2Result(
            status="not_computed",
            G_prime=G_prime,
            n_breaks=n_breaks,
            nonmissing_counts=nonmissing_counts,
            notes=[f"G'={G_prime} < G_min={g_min}; H2 not computed"],
        )

    # Fit within-sector regression (constant per segment) to get residuals
    # For H2, ε̂_{g,t} = z_{g,t} − ȳ_{g,seg(t)}
    residuals = sector_z.copy()
    for g in qualifying:
        for s, e in segs:
            mask = valid_mask[s:e, g]
            if mask.any():
                seg_mean = np.nanmean(sector_z[s:e, g][mask])
                residuals[s:e, g] = np.where(
                    valid_mask[s:e, g],
                    sector_z[s:e, g] - seg_mean,
                    np.nan,
                )

    # Build score matrix
    if n_breaks == 1:
        V = build_scores_one_break(residuals, tau1, valid_mask, qualifying)
    else:
        V = build_scores_two_break(residuals, tau1, tau2, valid_mask, qualifying)

    # Compute H2 bandwidth and HAC.
    # valid_mask[:, qualifying] aligns the (T, G') obs-mask with V's columns.
    # Per-sector AR(1) pilot uses only genuinely observed values (methods review §D.1).
    #
    # Two-break: V has shape (T, 2G') — episode 1 scores [0:G'] then episode 2
    # scores [G':2G'].  Each episode has a structurally-zero region:
    #   ep1 scores are zero for t >= tau2 (S3: not used by episode 1)
    #   ep2 scores are zero for t < tau1  (S1: not used by episode 2)
    # The AR(1) pilot for each episode must exclude those structural zeros so
    # the pilot fits only genuine observations from the episode's active segment.
    # Simple tiling (np.hstack([mask, mask])) would wrongly include S3 for ep1
    # and S1 for ep2, diluting the AR(1) estimate and biasing bandwidth down.
    valid_mask_q_single = valid_mask[:, qualifying]     # (T, G')
    if n_breaks == 1:
        valid_mask_q = valid_mask_q_single
    else:  # n_breaks == 2
        # Episode 1: active in S1∪S2 → exclude S3 (t >= tau2) from pilot
        ep1_mask = valid_mask_q_single.copy()
        ep1_mask[tau2:, :] = False
        # Episode 2: active in S2∪S3 → exclude S1 (t < tau1) from pilot
        ep2_mask = valid_mask_q_single.copy()
        ep2_mask[:tau1, :] = False
        valid_mask_q = np.hstack([ep1_mask, ep2_mask])   # (T, 2G')
    B_T = compute_h2_bandwidth(V, valid_mask_q)
    # Sigma_hat is the literal v1.0 §7 formula (no /T in autocovariance),
    # so it is already of order Var(Δ̂_g) = σ²/T. No T rescaling needed.
    Sigma_hat = multivariate_hac_scores(V, bandwidth=B_T)

    # Sector shift estimates (Δ̂)
    if n_breaks == 1:
        delta_hat = _sector_shift_estimates(
            sector_z, tau1, None, valid_mask, qualifying
        )
    else:
        delta_flat = _sector_shift_estimates(
            sector_z, tau1, tau2, valid_mask, qualifying
        )  # (G', 2)
        delta_hat = delta_flat.ravel(order='F')  # [ep1_all, ep2_all] — matches stacked Sigma

    wald = wald_test(delta_hat, Sigma_hat, G_prime, n_breaks)
    wald.hac_bandwidth = B_T
    wald.nonmissing_sector_month_counts = nonmissing_counts

    return H2Result(
        status=wald.status,
        G_prime=G_prime,
        n_breaks=n_breaks,
        wald=wald,
        nonmissing_counts=nonmissing_counts,
    )
