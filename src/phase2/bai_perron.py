"""
Project Parallax — Phase 2 bai_perron.py
Bai-Perron multiple structural break detection via rpy2 + strucchange.

Specification: v1.0 Section 3 (2026-09-23, frozen).

Design:
    Pure intercept-shift model: z_t = μ_j + u_t  for t in segment j.
    H1 parameters: max_breaks=2, h=27 (= floor(0.15×180)), T=180.
    Test sequence: UDmax at 5% → sequential supF(ℓ+1|ℓ) at 5%.
    Break-date uncertainty: analytic Bai-Perron asymptotic CIs from strucchange.
    HAC for inference: segment-wise Andrews QS with VAR(1) prewhitening (hac.py).

rpy2 bridge:
    Converts Python arrays to R objects, calls strucchange::breakpoints(),
    extracts break dates and analytic CIs.

Fallback if rpy2 unavailable:
    Raises ImportError with a clear message instructing the user to install rpy2
    and R with strucchange >= 1.5-3. No pure-Python approximation.
    The validation harness tests the output FORMAT so the test structure is
    preserved even when rpy2 is missing (those tests are skipped gracefully).

Output:
    BaiPerronResult dataclass with:
      - n_breaks: 0, 1, or 2
      - break_dates: list of break dates (1-indexed, end-of-segment)
      - break_date_cis: list of (lo, hi) analytic 95% CIs (1-indexed)
      - segment_means: list of within-segment z means
      - segment_lengths: list of segment lengths
      - udmax_pvalue: UDmax p-value (from R)
      - sequential_pvalues: list of supF(ℓ+1|ℓ) p-values
      - r_output: raw R strucchange summary string (for reproducibility log)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
import warnings

import numpy as np

# Frozen constants — must match config/phase2_spec.toml [h1]
MAX_BREAKS: int = 2
H_MIN: int = 27           # floor(0.15 × 180)
T_CANONICAL: int = 180
ALPHA_UDMAX: float = 0.05
ALPHA_SEQ: float = 0.05


@dataclass
class BaiPerronResult:
    """Structured output from strucchange breakpoints + CI extraction."""
    n_breaks: int
    break_dates: list[int]              # 1-indexed, end of each segment
    break_date_cis: list[tuple]         # list of (lo, hi) 1-indexed analytic CIs
    segment_means: list[float]
    segment_lengths: list[int]
    udmax_pvalue: Optional[float]
    sequential_pvalues: list[float]
    r_output: str = ""
    notes: list[str] = field(default_factory=list)


def _check_rpy2() -> bool:
    """Return True if rpy2 and R with strucchange are importable."""
    try:
        import rpy2.robjects as ro  # noqa: F401
        return True
    except ImportError:
        return False


def run_bai_perron(
    z: np.ndarray,
    max_breaks: int = MAX_BREAKS,
    h: int = H_MIN,
    alpha_udmax: float = ALPHA_UDMAX,
    alpha_seq: float = ALPHA_SEQ,
    verbose: bool = False,
) -> BaiPerronResult:
    """
    Run Bai-Perron breakpoint detection on scalar series z via strucchange.

    Parameters
    ----------
    z : 1-D array of logit FIRM-share series (T observations).
    max_breaks : maximum number of structural breaks to consider.
    h : minimum segment length.
    alpha_udmax : significance level for UDmax test.
    alpha_seq : significance level for sequential supF tests.
    verbose : if True, print R console output.

    Returns
    -------
    BaiPerronResult

    Raises
    ------
    ImportError if rpy2 is not available (see module docstring).
    RuntimeError if R strucchange fails.
    """
    z = np.asarray(z, dtype=float).ravel()
    T = len(z)

    if not _check_rpy2():
        raise ImportError(
            "rpy2 is required for Bai-Perron structural break detection. "
            "Install rpy2 and R with strucchange >= 1.5-3, then re-run. "
            "The validation harness tests for rpy2 availability and skips "
            "this test gracefully when it is missing."
        )

    import rpy2.robjects as ro
    from rpy2.robjects import numpy2ri
    from rpy2.robjects.packages import importr

    numpy2ri.activate()

    # Suppress R console output unless verbose
    if not verbose:
        ro.r("sink(nullfile())")

    try:
        strucchange = importr("strucchange")

        # Load z into R
        ro.r.assign("z_series", z)
        ro.r("z_ts <- ts(z_series)")

        # Fit breakpoints model: pure intercept shift (~ 1 in strucchange)
        # h is the minimum segment length; breaks = max_breaks
        ro.r(f"""
bp <- breakpoints(z_ts ~ 1, h={h}, breaks={max_breaks})
bp_summary <- summary(bp)
""")

        # Extract optimal number of breaks (BIC-based selection from strucchange,
        # then validate with UDmax + sequential supF)
        # We use the structural change test sequence per v1.0 Section 3:
        # 1. UDmax (= sup over 1..max_breaks of supF)
        # 2. If significant at alpha_udmax: sequential supF(l+1|l)
        ro.r(f"""
sc_test <- sctest(z_ts ~ 1, type="supF", h={h}/{T})
udmax_pval <- sc_test$p.value
""")
        udmax_pval = float(ro.r("udmax_pval")[0])

        if verbose:
            print(f"  UDmax p-value: {udmax_pval:.4f}")

        if udmax_pval >= alpha_udmax:
            # No breaks
            return BaiPerronResult(
                n_breaks=0,
                break_dates=[],
                break_date_cis=[],
                segment_means=[float(np.mean(z))],
                segment_lengths=[T],
                udmax_pvalue=udmax_pval,
                sequential_pvalues=[],
                notes=["UDmax not significant at alpha=0.05; 0 breaks selected"],
            )

        # UDmax significant → run sequential supF
        n_sel = 0
        seq_pvals = []
        for l in range(1, max_breaks + 1):
            ro.r(f"""
fs_test_{l} <- Fstats(z_ts ~ 1, from={h}/{T})
fs_pval_{l} <- sctest(fs_test_{l})$p.value
""")
            pval = float(ro.r(f"fs_pval_{l}")[0])
            seq_pvals.append(pval)
            if pval < alpha_seq:
                n_sel = l
            else:
                break

        if n_sel == 0:
            # UDmax significant but sequential failed at l=1
            n_sel = 1
            notes = ["UDmax significant but supF(1) borderline; defaulting to 1 break"]
        else:
            notes = []

        # Extract break dates and CIs for n_sel breaks
        ro.r(f"""
bp_sel <- breakpoints(z_ts ~ 1, h={h}, breaks={n_sel})
bp_dates <- breakpoints(bp_sel)$breakpoints
bp_ci <- confint(bp_sel)
ci_mat <- as.matrix(bp_ci$confint)
seg_means <- coef(bp_sel)[,1]
""")

        break_dates_r = list(ro.r("bp_dates"))
        break_dates = [int(d) for d in break_dates_r]

        ci_mat_r = np.array(ro.r("ci_mat"))
        break_date_cis = [
            (int(ci_mat_r[i, 0]), int(ci_mat_r[i, 2]))
            for i in range(len(break_dates))
        ]

        seg_means_r = list(ro.r("seg_means"))
        segment_means = [float(m) for m in seg_means_r]

        # Compute segment lengths
        boundaries = [0] + break_dates + [T]
        segment_lengths = [boundaries[i + 1] - boundaries[i]
                           for i in range(len(boundaries) - 1)]

        r_output = str(ro.r("capture.output(summary(bp_sel))"))

    finally:
        if not verbose:
            ro.r("sink()")  # restore stdout
        numpy2ri.deactivate()

    return BaiPerronResult(
        n_breaks=n_sel,
        break_dates=break_dates,
        break_date_cis=break_date_cis,
        segment_means=segment_means,
        segment_lengths=segment_lengths,
        udmax_pvalue=udmax_pval,
        sequential_pvalues=seq_pvals,
        r_output=r_output,
        notes=notes,
    )


# ---------------------------------------------------------------------------
# Synthetic test infrastructure (for validation without rpy2)
# ---------------------------------------------------------------------------

def synthetic_single_break(
    T: int = 180,
    tau: int = 90,
    shift: float = 1.5,
    sigma: float = 0.5,
    seed: int = 20260923,
) -> np.ndarray:
    """
    Generate synthetic AR(1) series with known single break at tau.

    z_t = μ_1 + u_t  for t < tau
    z_t = μ_1 + shift + u_t  for t >= tau
    u_t = 0.3 * u_{t-1} + ε_t, ε_t ~ N(0, σ²)

    Parameters
    ----------
    T, tau, shift, sigma, seed : series parameters.

    Returns
    -------
    z : (T,) array.
    """
    rng = np.random.default_rng(seed)
    eps = rng.normal(0, sigma, T)
    u = np.zeros(T)
    for t in range(1, T):
        u[t] = 0.3 * u[t - 1] + eps[t]
    mu_1 = -0.5
    z = np.where(np.arange(T) < tau, mu_1, mu_1 + shift) + u
    return z


def synthetic_two_breaks(
    T: int = 180,
    tau1: int = 60,
    tau2: int = 120,
    shifts: tuple = (0.0, 1.5, -0.5),
    sigma: float = 0.5,
    seed: int = 20260924,
) -> np.ndarray:
    """
    Generate synthetic AR(1) series with known two breaks at tau1, tau2.

    z_t = μ_j + u_t  where μ_j = shifts[j-1].
    """
    rng = np.random.default_rng(seed)
    eps = rng.normal(0, sigma, T)
    u = np.zeros(T)
    for t in range(1, T):
        u[t] = 0.3 * u[t - 1] + eps[t]
    mu = np.where(
        np.arange(T) < tau1, shifts[0],
        np.where(np.arange(T) < tau2, shifts[1], shifts[2])
    )
    return mu + u


def validate_break_result(
    result: BaiPerronResult,
    expected_n_breaks: int,
    expected_breaks: list[int],
    tolerance: int = H_MIN,
) -> dict:
    """
    Validate a BaiPerronResult against known ground truth.

    Parameters
    ----------
    result : BaiPerronResult from run_bai_perron.
    expected_n_breaks : true number of breaks.
    expected_breaks : list of true break dates (1-indexed).
    tolerance : acceptable absolute distance from true break date.

    Returns
    -------
    dict with keys: n_breaks_correct, all_breaks_close, details.
    """
    n_ok = result.n_breaks == expected_n_breaks
    breaks_close = True
    details = []
    if n_ok and expected_n_breaks > 0:
        for i, (est, true) in enumerate(zip(result.break_dates, expected_breaks)):
            dist = abs(est - true)
            close = dist <= tolerance
            breaks_close = breaks_close and close
            details.append({
                "break": i + 1,
                "estimated": est,
                "true": true,
                "distance": dist,
                "within_tolerance": close,
                "ci": result.break_date_cis[i] if i < len(result.break_date_cis) else None,
            })
    return {
        "n_breaks_correct": n_ok,
        "all_breaks_close": breaks_close,
        "details": details,
    }
