"""
Project Parallax — Phase 2 bootstrap.py
Circular Block Bootstrap (CBB) for H1 model-selection uncertainty.

Specification: v1.0 Section 4 (2026-09-23, frozen).

Design (frozen, do not alter):
    - B = 1999 replicates
    - L = 5 = floor(180^{1/3}) block length
    - SEED = 20260923
    - H1 stream: numpy.random.default_rng(SEED + 0)
    - SEED + 1: RESERVED AND UNUSED (H2 has no bootstrap)
    - SEED + 2: raw FIRM-share sensitivity (numpy.random.default_rng(SEED + 2))
    - Full-pipeline: breaks re-estimated inside every replicate (requires rpy2)
    - Same-break-count conditioning: replicates with different n_breaks from
      the observed series are used ONLY for frequency table (model-selection
      uncertainty). CIs conditioned on same-break-count subsets.
    - Chronological break matching: sort estimated breaks by date.
    - 200-replicate floor: if fewer than 200 same-count replicates, report
      "insufficient replicates" — NO fallback.
    - RNG objects passed explicitly; no global random state.

Output:
    BootstrapResult dataclass with:
      (A) break_count_frequency: dict {0: int, 1: int, 2: int} — model selection
      (B) break_date_cis: list of (lo, hi) bootstrap percentile CIs — NOT used for
          break-date uncertainty (that uses analytic Bai-Perron CIs per v1.0 §4)
      (C) segment_mean_cis: list of (lo, hi) for segment means — conditional CBB CIs
          on same-break-count replicates
      comparable_replicates: count of same-count replicates used for (C)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Callable

import numpy as np

# Frozen constants — must match config/phase2_spec.toml [bootstrap]
B: int = 1999
L: int = 5          # = floor(180^{1/3}) = floor(5.646) = 5
SEED: int = 20260923
COMPARABLE_REPLICATE_FLOOR: int = 200


@dataclass
class BootstrapResult:
    """
    Three distinct bootstrap estimands (separated, per v1.0 §4).

    (A) Model-selection uncertainty: frequency of 0/1/2 breaks.
    (B) Break-date uncertainty: NOT bootstrap (analytic Bai-Perron CIs used instead).
    (C) Break-magnitude uncertainty: conditional CBB CIs from same-break-count replicates.
    """
    # (A) Model-selection diagnostic
    break_count_frequency: dict        # {0: count, 1: count, 2: count}
    total_replicates: int              # = B = 1999

    # (C) Conditional CIs (same-break-count replicates)
    comparable_replicates: int         # must be >= 200
    segment_mean_cis: list[tuple]      # (lo, hi) 95% CI per segment

    # (B) Not bootstrap — field included for documentation only
    break_date_method: str = "analytic_bai_perron"  # never bootstrap

    # Diagnostics
    status: str = "ok"                 # "ok" | "insufficient_replicates"
    notes: list[str] = field(default_factory=list)
    seed_used: int = SEED


def cbb_resample(z: np.ndarray, L: int, rng: np.random.Generator) -> np.ndarray:
    """
    Circular Block Bootstrap resample of z.

    Blocks of length L are sampled with wrap-around:
        block starting at position i covers z[i:i+L] (mod T).

    Parameters
    ----------
    z : (T,) array — the series to resample.
    L : block length.
    rng : numpy.random.Generator — use the pre-seeded stream.

    Returns
    -------
    z_star : (T,) bootstrap sample.
    """
    T = len(z)
    n_blocks = int(np.ceil(T / L))
    starts = rng.integers(0, T, size=n_blocks)
    z_star = np.empty(n_blocks * L, dtype=z.dtype)
    for b, s in enumerate(starts):
        for j in range(L):
            z_star[b * L + j] = z[(s + j) % T]
    return z_star[:T]


def run_bootstrap(
    z: np.ndarray,
    break_detector: Callable[[np.ndarray], int],
    segment_stats: Callable[[np.ndarray, int], list[float]],
    observed_n_breaks: int,
    B: int = B,
    L: int = L,
    seed: int = SEED,
    comparable_floor: int = COMPARABLE_REPLICATE_FLOOR,
) -> BootstrapResult:
    """
    Full-pipeline CBB bootstrap for H1.

    Parameters
    ----------
    z : (T,) logit FIRM-share series (observed data).
    break_detector : callable(z_star) → int — re-estimates n_breaks on a
                     bootstrap replicate (wraps run_bai_perron).
    segment_stats : callable(z_star, n_b) → list[float] — computes segment
                    means for a replicate with n_b breaks; returns segment
                    mean vector conditional on same n_b.
    observed_n_breaks : n_breaks from the observed series (for conditioning).
    B, L, seed, comparable_floor : match frozen spec constants.

    Returns
    -------
    BootstrapResult

    Notes
    -----
    The RNG stream for H1 bootstrap is rng = numpy.random.default_rng(SEED + 0).
    SEED + 1 is reserved and unused. SEED + 2 is for raw-share sensitivity.
    This function accepts seed as a parameter so tests can vary it; production
    calls always pass SEED + 0.
    """
    rng = np.random.default_rng(seed)
    z = np.asarray(z, dtype=float).ravel()
    T = len(z)

    freq: dict[int, int] = {0: 0, 1: 0, 2: 0}
    comparable_seg_means: list[list[float]] = []
    notes: list[str] = []

    for b in range(B):
        z_star = cbb_resample(z, L, rng)
        try:
            n_b = break_detector(z_star)
        except Exception as e:
            notes.append(f"Replicate {b}: break_detector error: {e}")
            n_b = 0  # count as 0-break for frequency table

        freq[n_b] = freq.get(n_b, 0) + 1

        # Conditional segment statistics
        if n_b == observed_n_breaks:
            try:
                segs = segment_stats(z_star, n_b)
                comparable_seg_means.append(segs)
            except Exception as e:
                notes.append(f"Replicate {b}: segment_stats error: {e}")

    comparable_replicates = len(comparable_seg_means)

    if comparable_replicates < comparable_floor:
        return BootstrapResult(
            break_count_frequency={k: freq.get(k, 0) for k in (0, 1, 2)},
            total_replicates=B,
            comparable_replicates=comparable_replicates,
            segment_mean_cis=[],
            status="insufficient_replicates",
            notes=notes + [
                f"Only {comparable_replicates} same-count replicates "
                f"(floor={comparable_floor}). No fallback per v1.0 §4."
            ],
            seed_used=seed,
        )

    # 95% percentile CIs per segment from comparable replicates
    seg_mat = np.array(comparable_seg_means)  # (comparable, n_segs)
    segment_mean_cis = [
        (float(np.percentile(seg_mat[:, j], 2.5)),
         float(np.percentile(seg_mat[:, j], 97.5)))
        for j in range(seg_mat.shape[1])
    ]

    return BootstrapResult(
        break_count_frequency={k: freq.get(k, 0) for k in (0, 1, 2)},
        total_replicates=B,
        comparable_replicates=comparable_replicates,
        segment_mean_cis=segment_mean_cis,
        status="ok",
        notes=notes,
        seed_used=seed,
    )


# ---------------------------------------------------------------------------
# Synthetic break-detector for validation (without rpy2)
# ---------------------------------------------------------------------------

class SyntheticBreakDetector:
    """
    Minimal break detector using sum-of-squared-residuals for testing.
    NOT the production H1 detector (which uses rpy2/strucchange).
    Used solely for testing CBB machinery.
    """

    def __init__(self, h: int = L * 4, max_breaks: int = 2):
        self.h = h
        self.max_breaks = max_breaks

    def detect(self, z: np.ndarray) -> int:
        """Return 0, 1, or 2 based on BIC-penalised SSR reduction."""
        T = len(z)
        ssr_0 = float(np.sum((z - z.mean()) ** 2))
        best_n = 0
        best_bic = np.log(ssr_0 / T) + 0 / T * np.log(T)  # 0-break BIC proxy

        for n_b in range(1, self.max_breaks + 1):
            ssr_n = self._min_ssr(z, n_b)
            bic_n = np.log(ssr_n / T) + (n_b + 1) / T * np.log(T)
            if bic_n < best_bic:
                best_bic = bic_n
                best_n = n_b
        return best_n

    def _min_ssr(self, z: np.ndarray, n_breaks: int) -> float:
        """Crude exhaustive SSR minimisation (not Bai-Perron, for testing only)."""
        T = len(z)
        h = self.h
        if n_breaks == 1:
            best = np.inf
            for tau in range(h, T - h):
                s1 = z[:tau]; s2 = z[tau:]
                ssr = (np.sum((s1 - s1.mean()) ** 2) +
                       np.sum((s2 - s2.mean()) ** 2))
                if ssr < best:
                    best = ssr
            return best
        elif n_breaks == 2:
            best = np.inf
            for t1 in range(h, T - 2 * h):
                for t2 in range(t1 + h, T - h):
                    s1 = z[:t1]; s2 = z[t1:t2]; s3 = z[t2:]
                    ssr = (np.sum((s1 - s1.mean()) ** 2) +
                           np.sum((s2 - s2.mean()) ** 2) +
                           np.sum((s3 - s3.mean()) ** 2))
                    if ssr < best:
                        best = ssr
            return best
        return float(np.sum((z - z.mean()) ** 2))
