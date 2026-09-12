"""
Project Parallax — CLMX Variance Decomposition Regression Tests
================================================================

Documents and guards against the Option A missing-return defect discovered
during WP-05 Phase 1 hardening.

Background
----------
The CLMX decomposition produces three components per month:

    MKT_t  = sum_d  mu_d^2
    IND_t  = sum_j  W_j * sum_d  eta_{j,d}^2
    FIRM_t = sum_j  W_j * sum_i  w_{ij} * sum_d  eps_{i,j,d}^2

where mu_d is the daily VW market return, eta_{j,d} = r_{j,d} - mu_d is the
industry excess return, and eps_{i,j,d} = r_{i,d} - r_{j,d} is the
security-level residual.

Option A Latent Defect (discovered 2026-09)
-------------------------------------------
Under Option A (valid_days treatment), a stock may be present in the eligible
set for a month yet have NaN returns on some trading days within that month
(because it had fewer than the maximum trading days but still met the
min_valid_days threshold).

The defective implementation computed mu_d and r_j using
    R.mul(W, axis=1).sum(axis=1)      # pandas skipna=True → NaN treated as 0
but computed eps using
    R[ticker] - r_j                   # NaN for missing stock on missing day

Because (NaN ** 2).sum() skips the NaN terms, FIRM was understated by exactly
    sum_j W_j * w_ij * (r_{j,d})^2
for each positive-weight ticker that was missing on day d.

Under Option B (complete_month), R has no NaN by construction, so the defect
had zero impact on any canonical Phase 1 result.  The defect also had zero
impact on all 45 A-exclusive ticker-months in the Phase 1 live run, because
all 45 had zero prior-month-end weight.

The fix: add R_filled = R.fillna(0.0) and use R_filled[ticker] in the eps
loop, making mu_d, r_j, and eps consistently zero-imputed.

Synthetic Case
--------------
Two stocks (A, B) in one industry, two trading days:

    Weights: W_A = 0.6, W_B = 0.4     (prior-month-end VW, sum = 1.0)
    Day 1:   r_A = 0.05, r_B = 0.03   (both present)
    Day 2:   r_A = 0.02, r_B = NaN    (B missing)

Analytical solution (zero-imputed throughout):
    mu_d1 = 0.6*0.05 + 0.4*0.03 = 0.042
    mu_d2 = 0.6*0.02 + 0.4*0.00 = 0.012
    r_j1  = 0.042  (one industry = market)
    r_j2  = 0.012
    eps_A_d1 = 0.05  - 0.042 =  0.008
    eps_A_d2 = 0.02  - 0.012 =  0.008
    eps_B_d1 = 0.03  - 0.042 = -0.012
    eps_B_d2 = 0.00  - 0.012 = -0.012   (zero-imputed; defective: NaN → skipped)

    FIRM_correct  = 0.6*(0.008^2 + 0.008^2) + 0.4*(0.012^2 + 0.012^2)
                  = 0.6*0.000128 + 0.4*0.000288
                  = 0.0000768 + 0.0001152
                  = 0.00019200

    FIRM_defective = 0.6*(0.008^2 + 0.008^2) + 0.4*(0.012^2)   # day-2 B skipped
                   = 0.0000768 + 0.4*0.000144
                   = 0.0000768 + 0.0000576
                   = 0.00013440

    Gap = -5.76e-05 = W_j * w_B * (r_{j,d2})^2 = 1.0 * 0.4 * 0.012^2

These tests are pure Python / NumPy / pandas — no network access required.

Canonical Implementation Tests (TestCanonicalImplementation)
------------------------------------------------------------
In addition to the oracle tests above, this module also calls the real
decompose_month_clmx() from diagnostics/wp05_live_diagnostic.py with the
same bounded synthetic case.  These tests will FAIL if the R_filled fix is
removed from the canonical implementation.  They are skipped only if the
module cannot be imported (e.g., matplotlib is missing from the environment,
which should not occur in the standard project environment).
"""

import importlib.util
import pathlib
import sys

import numpy as np
import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Canonical implementation import
# ---------------------------------------------------------------------------
# Load decompose_month_clmx directly from the diagnostic script via
# importlib.util.spec_from_file_location so that no __init__.py is required
# in diagnostics/ and no sys.path mutation is needed.
#
# _CANONICAL_IMPORT_ERROR is None on success; set to the error string if the
# module cannot be loaded (missing matplotlib or other dep).  Tests in
# TestCanonicalImplementation are skipped in that case only — they are NOT
# silently passing.  A code regression in the implementation causes an
# AssertionError, not a skip.

_DIAGNOSTICS_PATH = (
    pathlib.Path(__file__).resolve().parent.parent
    / 'diagnostics'
    / 'wp05_live_diagnostic.py'
)

try:
    _spec = importlib.util.spec_from_file_location(
        'wp05_live_diagnostic', _DIAGNOSTICS_PATH
    )
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    _canonical_decompose = _mod.decompose_month_clmx
    _CANONICAL_IMPORT_ERROR = None
except Exception as _e:
    _canonical_decompose = None
    _CANONICAL_IMPORT_ERROR = str(_e)

# ---------------------------------------------------------------------------
# Numerical tolerance
# ---------------------------------------------------------------------------

TOLERANCE_EXACT = 1e-10   # component identity
TOLERANCE_GAP   = 1e-12   # gap formula


# ---------------------------------------------------------------------------
# Synthetic data construction
# ---------------------------------------------------------------------------

def _make_synthetic_inputs():
    """
    Build daily_returns-equivalent arrays for the 2-stock / 2-day case.

    Returns (R, W, w_ij) where:
        R    : pd.DataFrame, index=[day1, day2], columns=['A', 'B']
        W    : pd.Series, index=['A', 'B']   (already normalised, sum=1)
        w_ij : pd.Series  (within-industry normalised weights, sum=1)
    """
    idx = pd.DatetimeIndex(['2021-01-04', '2021-01-05'])
    R = pd.DataFrame(
        {'A': [0.05, 0.02], 'B': [0.03, np.nan]},
        index=idx,
    )
    W = pd.Series({'A': 0.6, 'B': 0.4})   # prior-month-end VW, sum = 1.0
    w_ij = W / W.sum()                    # same (one industry = whole market)
    return R, W, w_ij


# ---------------------------------------------------------------------------
# CLMX FIRM computation — two implementations
# ---------------------------------------------------------------------------

def _firm_defective(R, W, w_ij):
    """
    DEFECTIVE implementation: eps uses R[ticker] directly.
    NaN on missing days → (NaN**2).sum() silently skips those days.
    This is the pre-fix code path in decompose_month_clmx().
    """
    mu_d = R.mul(W, axis=1).sum(axis=1)   # skipna=True: NaN → 0 for mu_d
    members = list(R.columns)
    W_j = float(W[members].sum())
    r_j = R[members].mul(w_ij, axis=1).sum(axis=1)   # skipna=True
    FIRM = 0.0
    for ticker in members:
        eps = R[ticker] - r_j              # NaN on missing days → silently skipped
        FIRM += W_j * float(w_ij[ticker]) * float((eps ** 2).sum())
    return FIRM, mu_d


def _firm_correct(R, W, w_ij):
    """
    CORRECT implementation: R_filled = R.fillna(0.0) for eps.
    mu_d, r_j, and eps are all consistently zero-imputed.
    This is the post-fix code path in decompose_month_clmx().
    """
    R_filled = R.fillna(0.0)
    mu_d = R_filled.mul(W, axis=1).sum(axis=1)
    members = list(R.columns)
    W_j = float(W[members].sum())
    r_j = R_filled[members].mul(w_ij, axis=1).sum(axis=1)
    FIRM = 0.0
    for ticker in members:
        eps = R_filled[ticker] - r_j      # 0 on missing days: no NaN skip
        FIRM += W_j * float(w_ij[ticker]) * float((eps ** 2).sum())
    return FIRM, mu_d


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestOptionADefectRegression:
    """
    Regression suite for the Option A missing-return defect.

    These tests document the defect (2026-09 discovery) and guard against
    its reintroduction.  They do not constitute evidence about H1.
    """

    def test_defective_understates_firm(self):
        """
        The defective implementation gives FIRM = 0.00013440 — lower than the
        analytically correct value because eps is NaN on the missing day for
        stock B and that term is silently dropped from the sum.
        """
        R, W, w_ij = _make_synthetic_inputs()
        firm, _ = _firm_defective(R, W, w_ij)
        expected_defective = 0.00013440
        assert abs(firm - expected_defective) < TOLERANCE_EXACT, (
            f"Defective FIRM should be {expected_defective:.8f}, got {firm:.8f}"
        )

    def test_correct_firm_value(self):
        """
        The corrected implementation gives FIRM = 0.00019200 — the analytically
        derived value when missing returns are consistently zero-imputed.
        """
        R, W, w_ij = _make_synthetic_inputs()
        firm, _ = _firm_correct(R, W, w_ij)
        expected_correct = 0.00019200
        assert abs(firm - expected_correct) < TOLERANCE_EXACT, (
            f"Correct FIRM should be {expected_correct:.8f}, got {firm:.8f}"
        )

    def test_gap_equals_formula(self):
        """
        The gap between defective and correct FIRM equals the analytical formula:
            gap = W_j * w_B * (r_{j,d2})^2
                = 1.0 * 0.4 * 0.012^2
                = 5.76e-05
        """
        R, W, w_ij = _make_synthetic_inputs()
        firm_def, _ = _firm_defective(R, W, w_ij)
        firm_cor, _ = _firm_correct(R, W, w_ij)
        gap = firm_def - firm_cor
        expected_gap = -(1.0 * 0.4 * 0.012 ** 2)   # = -5.76e-05
        assert abs(gap - expected_gap) < TOLERANCE_GAP, (
            f"Gap should be {expected_gap:.2e}, got {gap:.2e}"
        )

    def test_defective_and_correct_are_different(self):
        """
        The two implementations must produce different FIRM values for this
        synthetic case, confirming the test distinguishes them.
        """
        R, W, w_ij = _make_synthetic_inputs()
        firm_def, _ = _firm_defective(R, W, w_ij)
        firm_cor, _ = _firm_correct(R, W, w_ij)
        assert firm_def != firm_cor, (
            "Defective and correct implementations gave identical FIRM — "
            "the synthetic case no longer exercises the defect."
        )

    def test_correct_is_larger(self):
        """
        The correct FIRM must exceed the defective FIRM for positive-weight
        missing stock: the defective code understates, never overstates.
        """
        R, W, w_ij = _make_synthetic_inputs()
        firm_def, _ = _firm_defective(R, W, w_ij)
        firm_cor, _ = _firm_correct(R, W, w_ij)
        assert firm_cor > firm_def, (
            "Correct FIRM should exceed defective FIRM; defect causes understatement."
        )

    def test_mkt_identical_both_implementations(self):
        """
        MKT must be identical under both implementations for this case.
        R.mul(W).sum(skipna=True) and R_filled.mul(W).sum() produce the same mu_d.
        Both treat NaN returns as zero: skipna=True in the defective path,
        explicit fillna in the correct path.
        """
        R, W, w_ij = _make_synthetic_inputs()
        _, mu_def = _firm_defective(R, W, w_ij)
        _, mu_cor = _firm_correct(R, W, w_ij)
        mkt_def = float((mu_def ** 2).sum())
        mkt_cor = float((mu_cor ** 2).sum())
        assert abs(mkt_def - mkt_cor) < TOLERANCE_EXACT, (
            f"MKT should be identical under both paths: def={mkt_def}, cor={mkt_cor}"
        )

    def test_option_b_unaffected(self):
        """
        Under Option B (complete_month), R has no NaN.  Both implementations
        give the same result, confirming the defect has zero impact on the
        canonical Phase 1 empirical result.
        """
        R, W, w_ij = _make_synthetic_inputs()
        # Option B: only stocks present every day — B is excluded (missing day 2)
        R_b = R[['A']].copy()
        W_b = pd.Series({'A': 1.0})   # renormalised to only stock present
        w_ij_b = pd.Series({'A': 1.0})
        firm_def, _ = _firm_defective(R_b, W_b, w_ij_b)
        firm_cor, _ = _firm_correct(R_b, W_b, w_ij_b)
        assert abs(firm_def - firm_cor) < TOLERANCE_EXACT, (
            "Under Option B (no NaN), both implementations must give identical FIRM."
        )

    def test_no_nan_case_unaffected(self):
        """
        When R has no NaN (e.g., Option B panel or a complete-data month),
        fillna(0.0) is a no-op and both implementations give identical results.
        """
        idx = pd.DatetimeIndex(['2021-01-04', '2021-01-05'])
        R_full = pd.DataFrame(
            {'A': [0.05, 0.02], 'B': [0.03, 0.01]},   # B present on day 2
            index=idx,
        )
        W = pd.Series({'A': 0.6, 'B': 0.4})
        w_ij = W / W.sum()
        firm_def, _ = _firm_defective(R_full, W, w_ij)
        firm_cor, _ = _firm_correct(R_full, W, w_ij)
        assert abs(firm_def - firm_cor) < TOLERANCE_EXACT, (
            "When R has no NaN, both paths must give identical FIRM."
        )


# ---------------------------------------------------------------------------
# Canonical implementation tests
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    _CANONICAL_IMPORT_ERROR is not None,
    reason=(
        f"diagnostics/wp05_live_diagnostic.py could not be imported "
        f"({_CANONICAL_IMPORT_ERROR}). Install full project requirements."
    ),
)
class TestCanonicalImplementation:
    """
    Tests that call the ACTUAL decompose_month_clmx() from
    diagnostics/wp05_live_diagnostic.py with the bounded synthetic case.

    These tests will FAIL — not skip — if the R_filled fix is removed from
    the canonical implementation.  Skipping occurs only when the diagnostic
    module itself cannot be imported (missing matplotlib or other dep not
    installed), which should not occur in the standard project environment.

    Synthetic case matches TestOptionADefectRegression exactly:
        Stocks A and B, one industry (both stocks = market).
        Weights: W_A = 0.6, W_B = 0.4 (from prior-month-end market caps).
        Day 1: r_A = 0.05, r_B = 0.03  (both present)
        Day 2: r_A = 0.02, r_B = NaN   (B missing)
        missing_treatment='valid_days', min_valid_days=1

    Expected (zero-imputed, corrected):
        MKT  = 0.042^2 + 0.012^2 = 0.001908
        IND  = 0  (one industry = whole market, eta = 0 everywhere)
        FIRM = 0.00019200
    """

    @staticmethod
    def _make_canonical_inputs():
        """
        Build the three DataFrames required by decompose_month_clmx().

        daily_returns : 2-day × 2-ticker return matrix for January 2021.
                        B is NaN on day 2.
        approx_mktcap : December 2020 market caps → prior-month-end weights
                        0.6 (A) / 0.4 (B) after normalization.
        ticker_industry: both tickers assigned to industry_num = 1.
        """
        idx = pd.DatetimeIndex(['2021-01-04', '2021-01-05'])
        daily_returns = pd.DataFrame(
            {'A': [0.05, 0.02], 'B': [0.03, np.nan]},
            index=idx,
        )
        # Prior-month-end: last trading day of December 2020.
        # Values 600 / 400 normalise to weights 0.6 / 0.4.
        approx_mktcap = pd.DataFrame(
            {'A': [600.0], 'B': [400.0]},
            index=pd.DatetimeIndex(['2020-12-31']),
        )
        ticker_industry = pd.DataFrame(
            {'industry_num': [1, 1]},
            index=['A', 'B'],
        )
        return daily_returns, approx_mktcap, ticker_industry

    def test_canonical_option_a_firm_zero_imputation(self):
        """
        The canonical implementation must return FIRM = 0.00019200 for this
        case (the analytically correct zero-imputed value).

        This test FAILS if the R_filled fix is reverted: without it,
        (NaN**2).sum() silently drops B's day-2 contribution and FIRM
        collapses to 0.00013440.
        """
        daily_returns, approx_mktcap, ticker_industry = self._make_canonical_inputs()

        result = _canonical_decompose(
            daily_returns=daily_returns,
            approx_mktcap=approx_mktcap,
            ticker_industry=ticker_industry,
            year=2021,
            month=1,
            missing_treatment='valid_days',  # Option A: B qualifies despite NaN on day 2
            min_valid_days=1,                # B has 1 valid return (day 1)
        )

        assert result is not None, (
            "decompose_month_clmx() returned None for a valid synthetic input. "
            "Check that the weight and eligibility logic accepts this case."
        )

        expected_correct   = 0.00019200
        expected_defective = 0.00013440

        assert abs(result['FIRM'] - expected_correct) < TOLERANCE_EXACT, (
            f"Canonical FIRM should be {expected_correct:.8f} (zero-imputed). "
            f"Got {result['FIRM']:.8f}. "
            f"If result ≈ {expected_defective:.8f}, the R_filled fix has been removed."
        )

    def test_canonical_mkt_matches_oracle(self):
        """
        MKT from the canonical implementation must match the analytically
        derived value: mu_d1^2 + mu_d2^2 = 0.042^2 + 0.012^2 = 0.001908.
        """
        daily_returns, approx_mktcap, ticker_industry = self._make_canonical_inputs()

        result = _canonical_decompose(
            daily_returns=daily_returns,
            approx_mktcap=approx_mktcap,
            ticker_industry=ticker_industry,
            year=2021,
            month=1,
            missing_treatment='valid_days',
            min_valid_days=1,
        )

        assert result is not None
        expected_mkt = 0.042 ** 2 + 0.012 ** 2   # = 0.001908
        assert abs(result['MKT'] - expected_mkt) < TOLERANCE_EXACT, (
            f"Canonical MKT should be {expected_mkt:.8f}, got {result['MKT']:.8f}."
        )

    def test_canonical_ind_is_zero(self):
        """
        IND must be zero: with one industry that spans the whole market,
        r_j = mu_d on every day, so eta = 0 everywhere.
        """
        daily_returns, approx_mktcap, ticker_industry = self._make_canonical_inputs()

        result = _canonical_decompose(
            daily_returns=daily_returns,
            approx_mktcap=approx_mktcap,
            ticker_industry=ticker_industry,
            year=2021,
            month=1,
            missing_treatment='valid_days',
            min_valid_days=1,
        )

        assert result is not None
        assert abs(result['IND']) < TOLERANCE_EXACT, (
            f"Canonical IND should be 0.0 (one industry = market), got {result['IND']:.2e}."
        )
