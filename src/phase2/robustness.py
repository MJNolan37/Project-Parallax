"""
Project Parallax — Phase 2 robustness.py
Raw FIRM-share sensitivity analysis.

Specification: v1.0 Section 5 (2026-09-23, frozen).

Design (frozen, do not alter):
    - Uses SEED+2 = 20260925 random stream (numpy.random.default_rng(SEED+2))
    - Runs Bai-Perron on the raw FIRM share s_t (not logit-transformed)
    - CBB bootstrap on raw s_t using the SEED+2 stream
    - Identical structural parameters to primary analysis (max=2, h=27, α=0.05)
    - Results written to data/phase2_robustness_results.json via reporting.py
    - DOES NOT re-use or share the SEED+0 stream

Boundary note:
    Raw FIRM share s_t ∈ (0, 1) by Phase 1 cap. The Bai-Perron test on s_t
    directly is level-shift detection in the share space. No logit transform.
    Results are therefore NOT directly comparable to H1 (which operates on z_t).
    This analysis documents sensitivity, not an alternative inference.

Stop-gate:
    This module does NOT open the empirical gate. It is part of the
    robustness arm; the primary H1/H2 gate applies independently.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from .bootstrap import (
    SEED,
    B,
    L,
    COMPARABLE_REPLICATE_FLOOR,
    BootstrapResult,
    cbb_resample,
)

# SEED+2 stream (v1.0 §5) — never share with SEED+0 (H1 primary)
ROBUSTNESS_SEED: int = SEED + 2   # = 20260925


# ---------------------------------------------------------------------------
# CBB bootstrap on raw share (mirror of bootstrap.py run_bootstrap, SEED+2)
# ---------------------------------------------------------------------------

def run_robustness_bootstrap(
    s_t: np.ndarray,
    observed_n_breaks: int,
    break_estimator: callable,
    n_replicates: int = B,
    block_length: int = L,
    seed: int = ROBUSTNESS_SEED,
) -> BootstrapResult:
    """
    CBB bootstrap on raw FIRM share s_t using SEED+2 stream.

    This is a structural mirror of bootstrap.run_bootstrap but
    for the raw-share sensitivity arm (v1.0 §5).

    Parameters
    ----------
    s_t : T-length array of raw FIRM share values (s_t in (0,1)).
    observed_n_breaks : n_breaks from the primary raw-share Bai-Perron run.
    break_estimator : callable(z) → BaiPerronResult.
                      Must accept raw share series (no logit transform here).
    n_replicates : number of CBB replicates (frozen at B=1999).
    block_length : CBB block length (frozen at L=5).
    seed : RNG seed (frozen at ROBUSTNESS_SEED = SEED+2 = 20260925).

    Returns
    -------
    BootstrapResult
    """
    rng = np.random.default_rng(seed)
    T = len(s_t)

    break_count_frequency: dict[int, int] = {0: 0, 1: 0, 2: 0}
    all_segment_means: list[list[float]] = [[] for _ in range(observed_n_breaks + 1)]
    comparable_replicates = 0
    notes: list[str] = []

    for _ in range(n_replicates):
        s_star = cbb_resample(s_t, block_length, rng)
        try:
            result = break_estimator(s_star)
        except Exception:
            break_count_frequency[0] = break_count_frequency.get(0, 0) + 1
            continue

        n_b = result.n_breaks
        count_key = min(n_b, 2)  # cap at 2 for frequency table
        break_count_frequency[count_key] = (
            break_count_frequency.get(count_key, 0) + 1
        )

        # Conditional on same break count
        if n_b == observed_n_breaks:
            comparable_replicates += 1
            for seg_idx, seg_mean in enumerate(result.segment_means):
                if seg_idx < len(all_segment_means):
                    all_segment_means[seg_idx].append(float(seg_mean))

    # Compute 95% CIs from conditional replicates
    status = "ok"
    segment_mean_cis: list[tuple[float, float]] = []

    if comparable_replicates < COMPARABLE_REPLICATE_FLOOR:
        status = "insufficient_replicates"
        notes.append(
            f"Only {comparable_replicates} comparable replicates "
            f"(floor={COMPARABLE_REPLICATE_FLOOR}). "
            "Segment-mean CIs not computed."
        )
        segment_mean_cis = [(float("nan"), float("nan"))] * (observed_n_breaks + 1)
    else:
        for seg_means in all_segment_means:
            if len(seg_means) >= 2:
                lo = float(np.percentile(seg_means, 2.5))
                hi = float(np.percentile(seg_means, 97.5))
                segment_mean_cis.append((lo, hi))
            else:
                segment_mean_cis.append((float("nan"), float("nan")))
                notes.append("Insufficient segment samples for one CI.")

    # Ensure all n_breaks keys are present
    for k in (0, 1, 2):
        break_count_frequency.setdefault(k, 0)

    return BootstrapResult(
        break_count_frequency=break_count_frequency,
        total_replicates=n_replicates,
        comparable_replicates=comparable_replicates,
        segment_mean_cis=segment_mean_cis,
        break_date_method="analytic_bai_perron",  # (B) always analytic
        status=status,
        notes=notes,
        seed_used=seed,
    )


# ---------------------------------------------------------------------------
# Robustness run entry point (pure-Python, no empirical data)
# ---------------------------------------------------------------------------

def run_robustness(
    s_t: np.ndarray,
    break_estimator: callable,
    h2_runner: Optional[callable] = None,
    valid_mask: Optional[np.ndarray] = None,
) -> dict:
    """
    Run raw-share sensitivity analysis (v1.0 §5, SEED+2 stream).

    Parameters
    ----------
    s_t : T-length array of raw FIRM share values.
          Caller must supply the FIRM share column from Phase 1 CSV.
    break_estimator : callable(s) → BaiPerronResult.
                      Same structural parameters as primary (max=2, h=27).
    h2_runner : optional callable(sector_s, valid_mask, break_dates) → H2Result.
                If None, H2 is not run for the robustness arm.
    valid_mask : (T, G) boolean mask for sector coverage (for H2).

    Returns
    -------
    dict with keys:
        "bp" : BaiPerronResult from Bai-Perron on s_t
        "bootstrap" : BootstrapResult from CBB on s_t (SEED+2)
        "h2" : H2Result (or None if h2_runner not supplied)
        "seed" : ROBUSTNESS_SEED
    """
    # Primary Bai-Perron on raw share
    bp_result = break_estimator(s_t)

    # CBB bootstrap on raw share using SEED+2
    bootstrap_result = run_robustness_bootstrap(
        s_t,
        observed_n_breaks=bp_result.n_breaks,
        break_estimator=break_estimator,
        seed=ROBUSTNESS_SEED,
    )

    # H2 on raw share (optional)
    h2_result = None
    if h2_runner is not None and valid_mask is not None and bp_result.n_breaks > 0:
        h2_result = h2_runner(
            s_t if valid_mask.ndim == 1 else None,
            valid_mask,
            bp_result.break_dates,
        )

    return {
        "bp": bp_result,
        "bootstrap": bootstrap_result,
        "h2": h2_result,
        "seed": ROBUSTNESS_SEED,
    }


# ---------------------------------------------------------------------------
# Synthetic data generator for harness testing (no empirical data)
# ---------------------------------------------------------------------------

def synthetic_raw_share(
    T: int = 180,
    tau: int = 90,
    shift: float = 0.1,
    base: float = 0.35,
    sigma: float = 0.02,
    seed: int = 20260925,
) -> np.ndarray:
    """
    Synthetic raw FIRM share series for harness testing.

    Piecewise-constant mean plus Gaussian noise, clipped to (0.01, 0.99).

    Parameters
    ----------
    T : series length.
    tau : break point (1-indexed, i.e., break AFTER observation tau).
    shift : level shift in the share (post-break mean = base + shift).
    base : pre-break mean level.
    sigma : noise standard deviation.
    seed : RNG seed.

    Returns
    -------
    s_t : np.ndarray of shape (T,), values in (0.01, 0.99).
    """
    rng = np.random.default_rng(seed)
    noise = rng.normal(0.0, sigma, T)
    s = np.empty(T)
    s[:tau] = base + noise[:tau]
    s[tau:] = base + shift + noise[tau:]
    # Clip to open interval matching Phase 1 boundary cap
    return np.clip(s, 0.01, 0.99)
