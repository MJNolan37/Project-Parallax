"""
Tests for src/phase2/transform.py
Phase 2.1 validation harness — known-answer tests for FIRM-share transformation.

All tests use synthetic data only. No empirical data accessed.
v1.0 Section 2 specification.
"""
import math
import pytest
import numpy as np
import pandas as pd

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.phase2.transform import (
    BOUNDARY_LOWER,
    BOUNDARY_UPPER,
    DataQualityError,
    TransformResult,
    compute_z_series,
    back_transform_ci,
    firm_share,
    inv_logit,
    logit_share,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_df(mkt, ind, firm, n=None):
    """Build synthetic monthly DataFrame with DatetimeIndex."""
    if n is None:
        n = len(mkt)
    dates = pd.date_range("2010-01-01", periods=n, freq="MS")
    return pd.DataFrame({"MKT": mkt, "IND": ind, "FIRM": firm}, index=dates)


# ---------------------------------------------------------------------------
# 1. firm_share scalar identity
# ---------------------------------------------------------------------------

class TestFirmShare:
    def test_scalar_interior(self):
        s = firm_share(0.3, 0.2, 0.5)
        assert abs(s - 0.5) < 1e-12

    def test_scalar_equal_parts(self):
        s = firm_share(1.0, 1.0, 1.0)
        assert abs(s - 1.0 / 3.0) < 1e-12

    def test_array(self):
        mkt = np.array([0.3, 0.4])
        ind = np.array([0.2, 0.1])
        firm = np.array([0.5, 0.5])
        s = firm_share(mkt, ind, firm)
        np.testing.assert_allclose(s, [0.5, 0.5], rtol=1e-12)

    def test_near_zero(self):
        # Small firm share
        s = firm_share(99.0, 0.9, 0.1)
        assert abs(s - 0.1 / 100.0) < 1e-12


# ---------------------------------------------------------------------------
# 2. logit / inv_logit round-trip
# ---------------------------------------------------------------------------

class TestLogitInvLogit:
    def test_round_trip_scalar(self):
        for s in [0.1, 0.3, 0.5, 0.7, 0.9]:
            z = logit_share(s)
            assert abs(inv_logit(z) - s) < 1e-12

    def test_round_trip_array(self):
        s = np.array([0.01, 0.25, 0.5, 0.75, 0.99])
        z = logit_share(s)
        np.testing.assert_allclose(inv_logit(z), s, rtol=1e-12)

    def test_logit_at_half(self):
        assert abs(logit_share(0.5)) < 1e-12

    def test_logit_known_values(self):
        # logit(0.75) = log(3) ≈ 1.0986122886681098
        assert abs(logit_share(0.75) - math.log(3)) < 1e-12


# ---------------------------------------------------------------------------
# 3. Boundary handling — halt conditions
# ---------------------------------------------------------------------------

class TestBoundaryHalt:
    def test_exact_zero_firm_halts(self):
        df = _make_df([1.0], [1.0], [0.0])
        with pytest.raises(DataQualityError, match="exactly 0"):
            compute_z_series(df)

    def test_exact_one_firm_halts(self):
        # FIRM = total → s = 1 exactly
        df = _make_df([0.0], [0.0], [1.0])
        with pytest.raises(DataQualityError, match="exactly 1"):
            compute_z_series(df)

    def test_mkt_ind_zero_halts(self):
        # s = FIRM / (0 + 0 + FIRM) = 1.0
        df = _make_df([0.0], [0.0], [5.0])
        with pytest.raises(DataQualityError):
            compute_z_series(df)


# ---------------------------------------------------------------------------
# 4. Boundary handling — cap conditions (no halt)
# ---------------------------------------------------------------------------

class TestBoundaryCap:
    def test_lower_cap_applied(self):
        """FIRM share just below 1e-6 → capped to 1e-6, no error."""
        firm_val = 1e-10   # s ≈ 1e-10 / 1.0 = 1e-10 < 1e-6
        df = _make_df([1.0 - 1e-10], [0.0], [1e-10])
        result = compute_z_series(df)
        assert len(result.cap_events) == 1
        cap = result.cap_events[0]
        assert cap["side"] == "lower"
        assert abs(cap["s_capped"] - BOUNDARY_LOWER) < 1e-18
        # z should equal logit(1e-6)
        expected_z = math.log(BOUNDARY_LOWER / (1.0 - BOUNDARY_LOWER))
        assert abs(result.z[0] - expected_z) < 1e-10

    def test_upper_cap_applied(self):
        """FIRM share just above 1 - 1e-6 → capped to 1 - 1e-6, no error."""
        firm_val = 1.0 - 1e-10
        df = _make_df([1e-10 / 2], [1e-10 / 2], [1.0 - 1e-10])
        result = compute_z_series(df)
        assert len(result.cap_events) == 1
        cap = result.cap_events[0]
        assert cap["side"] == "upper"
        assert abs(cap["s_capped"] - BOUNDARY_UPPER) < 1e-18

    def test_no_cap_in_interior(self):
        """Interior values: no cap events."""
        n = 5
        mkt_vals = np.full(n, 0.4)
        ind_vals = np.full(n, 0.2)
        firm_vals = np.full(n, 0.4)   # s = 0.4 everywhere
        df = _make_df(mkt_vals, ind_vals, firm_vals)
        result = compute_z_series(df)
        assert result.cap_events == []
        # z should equal logit(0.4) = log(0.4/0.6) = log(2/3)
        expected_z = math.log(2.0 / 3.0)
        np.testing.assert_allclose(result.z, expected_z, rtol=1e-12)


# ---------------------------------------------------------------------------
# 5. Known-answer z values (interior)
# ---------------------------------------------------------------------------

class TestKnownAnswerZ:
    def test_equal_shares(self):
        """If MKT = IND = FIRM → s = 1/3 → z = log(0.5) = -log(2)"""
        df = _make_df([1.0], [1.0], [1.0])
        result = compute_z_series(df)
        expected = math.log(1.0 / 2.0)  # logit(1/3) = log((1/3)/(2/3)) = log(1/2)
        assert abs(result.z[0] - expected) < 1e-12

    def test_firm_dominant(self):
        """FIRM = 3×(MKT+IND) → s = 3/4 → z = log(3) ≈ 1.0986"""
        df = _make_df([0.25], [0.25], [1.5])
        result = compute_z_series(df)
        # s = 1.5/2.0 = 0.75; z = log(0.75/0.25) = log(3)
        expected = math.log(3.0)
        assert abs(result.z[0] - expected) < 1e-12

    def test_series_length_180(self):
        """Mimics the canonical T=180 case structure."""
        n = 180
        mkt_vals = np.random.default_rng(42).uniform(0.05, 0.5, n)
        ind_vals = np.random.default_rng(43).uniform(0.05, 0.3, n)
        firm_vals = np.random.default_rng(44).uniform(0.05, 0.4, n)
        df = _make_df(mkt_vals, ind_vals, firm_vals)
        result = compute_z_series(df)
        assert result.z.shape == (180,)
        assert len(result.dates) == 180
        assert result.cap_events == []
        # Verify z = logit(s) for all t
        s_computed = result.s
        z_expected = np.log(s_computed / (1.0 - s_computed))
        np.testing.assert_allclose(result.z, z_expected, rtol=1e-12)


# ---------------------------------------------------------------------------
# 6. Back-transform CI round-trip
# ---------------------------------------------------------------------------

class TestBackTransformCI:
    def test_known_answer(self):
        """Back-transform of logit CI recovers original share bounds."""
        s_lo, s_hi = 0.2, 0.6
        z_lo = logit_share(s_lo)
        z_hi = logit_share(s_hi)
        s_lo_back, s_hi_back = back_transform_ci(z_lo, z_hi)
        assert abs(s_lo_back - s_lo) < 1e-12
        assert abs(s_hi_back - s_hi) < 1e-12

    def test_asymmetry_in_share_space(self):
        """A symmetric CI in z-space is asymmetric in s-space (logit nonlinearity)."""
        z_center = 0.0    # s = 0.5
        delta = 0.5
        s_lo, s_hi = back_transform_ci(z_center - delta, z_center + delta)
        assert s_lo < 0.5 < s_hi
        # Distance below 0.5 should equal distance above 0.5 (logit is symmetric at 0)
        assert abs((0.5 - s_lo) - (s_hi - 0.5)) < 1e-12

    def test_arrays(self):
        z_arr = np.array([-1.0, 0.0, 1.0])
        s_lo, s_hi = back_transform_ci(z_arr - 0.3, z_arr + 0.3)
        assert s_lo.shape == (3,) and s_hi.shape == (3,)
        np.testing.assert_array_less(s_lo, s_hi)


# ---------------------------------------------------------------------------
# 7. Non-positive total variance raises ValueError (not DataQualityError)
# ---------------------------------------------------------------------------

class TestNonPositiveTotal:
    def test_zero_total_raises(self):
        df = _make_df([0.0], [0.0], [0.0])
        with pytest.raises(ValueError, match="Non-positive total variance"):
            compute_z_series(df)
