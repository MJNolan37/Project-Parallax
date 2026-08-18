"""
Project Parallax — Known-Answer Brinson Attribution Tests
==========================================================

Validates the Brinson-Fachler attribution engine against synthetic portfolios
with fully deterministic expected outputs.

Design Principle
----------------
Attribution engines can fail silently. A plausible-looking output from an
incorrect implementation is more dangerous than an obvious error. These tests
enforce a validation gate: the engine must correctly explain portfolios we
deliberately constructed before it is applied to portfolios we did not.

If the attribution engine cannot correctly explain a portfolio we deliberately
constructed, it should not be trusted to explain a portfolio we did not.

Test Portfolio Architecture
---------------------------
Portfolio A — Pure Selection Effect
    Portfolio and benchmark hold identical sector weights.
    Intra-sector holdings differ: the portfolio overweights a high-return
    security in each sector relative to the benchmark.
    Expected outcome: large positive selection effect, near-zero allocation
    effect, interaction effect following from the method convention.

Portfolio B — Pure Allocation Effect
    Portfolio and benchmark hold identical securities within each sector.
    Sector weights differ: the portfolio overweights sectors with above-
    benchmark returns and underweights sectors with below-benchmark returns.
    Expected outcome: large positive allocation effect, near-zero selection
    effect.

Portfolio C — Combined Effects
    Both sector weights and within-sector holdings differ.
    Explicitly constructed so that the total attribution reconciles to the
    total active return within floating-point tolerance.
    Purpose: verify arithmetic integrity of the combined decomposition.

Validation Criteria
-------------------
1. Numerical accuracy — computed effects match expected values within
   tolerance = 1e-6 (six decimal places).
2. Reconciliation — sum of allocation + selection + interaction effects
   equals the computed active return within the same tolerance.
3. Sign correctness — effects are in the expected direction for the
   constructed scenario.
4. Zero-residual — the BrinsonResult.reconciliation_residual is near zero.

Notes
-----
These tests are stubs. The test cases, including all weights, returns, and
expected attribution values, are pre-computed analytically below and will
drive the implementation rather than be filled in after it.

Implementation is pending Phase 3 (Brinson Attribution Engine).
"""

import pytest
import pandas as pd
import numpy as np

from src.attribution.brinson import brinson_attribution, BrinsonResult


# ---------------------------------------------------------------------------
# Numerical tolerance
# ---------------------------------------------------------------------------

TOLERANCE = 1e-6


# ---------------------------------------------------------------------------
# Portfolio A — Pure Selection Effect
# ---------------------------------------------------------------------------
#
# Setup:
#   Two sectors: Tech (T), Non-Tech (N)
#   Sector weights identical in portfolio and benchmark: T=0.6, N=0.4
#
#   Tech securities: TECH_A (high return), TECH_B (low return)
#   Non-Tech securities: NTECH_A (high return), NTECH_B (low return)
#
#   Portfolio within-sector weights:
#     Tech:     TECH_A=0.75, TECH_B=0.25  (overweight high-return)
#     Non-Tech: NTECH_A=0.75, NTECH_B=0.25
#
#   Benchmark within-sector weights:
#     Tech:     TECH_A=0.50, TECH_B=0.50
#     Non-Tech: NTECH_A=0.50, NTECH_B=0.50
#
#   Returns:
#     TECH_A=0.10, TECH_B=0.02
#     NTECH_A=0.08, NTECH_B=0.01
#
# Computed expected values (hand-verified):
#
#   Benchmark sector returns:
#     Tech:     0.5*0.10 + 0.5*0.02 = 0.06
#     Non-Tech: 0.5*0.08 + 0.5*0.01 = 0.045
#
#   Portfolio sector returns:
#     Tech:     0.75*0.10 + 0.25*0.02 = 0.08
#     Non-Tech: 0.75*0.08 + 0.25*0.01 = 0.0625
#
#   Benchmark total return: 0.6*0.06 + 0.4*0.045 = 0.036 + 0.018 = 0.054
#   Portfolio total return: 0.6*0.08 + 0.4*0.0625 = 0.048 + 0.025 = 0.073
#   Active return: 0.073 - 0.054 = 0.019
#
#   Brinson-Fachler allocation effect (per sector):
#     = (wp_i - wb_i) * (Rb_i - Rb_total)
#     Tech:     (0.6 - 0.6) * (0.06 - 0.054) = 0.0
#     Non-Tech: (0.4 - 0.4) * (0.045 - 0.054) = 0.0
#
#   Selection effect (per sector):
#     = wb_i * (Rp_i - Rb_i)
#     Tech:     0.6 * (0.08 - 0.06) = 0.012
#     Non-Tech: 0.4 * (0.0625 - 0.045) = 0.007
#
#   Interaction effect (per sector):
#     = (wp_i - wb_i) * (Rp_i - Rb_i)
#     Tech:     (0.6 - 0.6) * (0.08 - 0.06) = 0.0
#     Non-Tech: (0.4 - 0.4) * (0.0625 - 0.045) = 0.0
#
#   Check: total selection = 0.012 + 0.007 = 0.019 ✓ matches active return


@pytest.fixture
def portfolio_a_inputs():
    """Inputs for Portfolio A (pure selection)."""
    tickers = ["TECH_A", "TECH_B", "NTECH_A", "NTECH_B"]

    portfolio_weights = pd.Series(
        [0.6 * 0.75, 0.6 * 0.25, 0.4 * 0.75, 0.4 * 0.25],
        index=tickers,
    )  # [0.45, 0.15, 0.30, 0.10]

    benchmark_weights = pd.Series(
        [0.6 * 0.50, 0.6 * 0.50, 0.4 * 0.50, 0.4 * 0.50],
        index=tickers,
    )  # [0.30, 0.30, 0.20, 0.20]

    returns = pd.Series(
        [0.10, 0.02, 0.08, 0.01],
        index=tickers,
    )

    group_map = pd.Series(
        ["Tech", "Tech", "Non-Tech", "Non-Tech"],
        index=tickers,
    )

    return portfolio_weights, benchmark_weights, returns, returns, group_map


@pytest.fixture
def portfolio_a_expected():
    """Expected attribution output for Portfolio A."""
    return {
        "total_allocation": 0.0,
        "total_selection": 0.019,
        "total_interaction": 0.0,
        "active_return": 0.019,
        "allocation_by_sector": {"Tech": 0.0, "Non-Tech": 0.0},
        "selection_by_sector": {"Tech": 0.012, "Non-Tech": 0.007},
        "interaction_by_sector": {"Tech": 0.0, "Non-Tech": 0.0},
    }


class TestPortfolioA:
    """Portfolio A: pure selection effect — no allocation or interaction."""

    @pytest.mark.xfail(reason="brinson_attribution pending Phase 3 implementation")
    def test_total_selection_effect(self, portfolio_a_inputs, portfolio_a_expected):
        pw, bw, pr, br, gm = portfolio_a_inputs
        result = brinson_attribution(pw, bw, pr, br, gm)
        assert isinstance(result, BrinsonResult)
        assert abs(result.total_selection - portfolio_a_expected["total_selection"]) < TOLERANCE

    @pytest.mark.xfail(reason="brinson_attribution pending Phase 3 implementation")
    def test_allocation_is_zero(self, portfolio_a_inputs, portfolio_a_expected):
        pw, bw, pr, br, gm = portfolio_a_inputs
        result = brinson_attribution(pw, bw, pr, br, gm)
        assert abs(result.total_allocation - portfolio_a_expected["total_allocation"]) < TOLERANCE

    @pytest.mark.xfail(reason="brinson_attribution pending Phase 3 implementation")
    def test_interaction_is_zero(self, portfolio_a_inputs, portfolio_a_expected):
        pw, bw, pr, br, gm = portfolio_a_inputs
        result = brinson_attribution(pw, bw, pr, br, gm)
        assert abs(result.total_interaction - portfolio_a_expected["total_interaction"]) < TOLERANCE

    @pytest.mark.xfail(reason="brinson_attribution pending Phase 3 implementation")
    def test_selection_by_sector(self, portfolio_a_inputs, portfolio_a_expected):
        pw, bw, pr, br, gm = portfolio_a_inputs
        result = brinson_attribution(pw, bw, pr, br, gm)
        expected_sel = portfolio_a_expected["selection_by_sector"]
        for sector, expected_val in expected_sel.items():
            assert abs(result.selection[sector] - expected_val) < TOLERANCE, (
                f"Selection effect for {sector}: got {result.selection[sector]}, "
                f"expected {expected_val}"
            )

    @pytest.mark.xfail(reason="brinson_attribution pending Phase 3 implementation")
    def test_reconciliation(self, portfolio_a_inputs):
        pw, bw, pr, br, gm = portfolio_a_inputs
        result = brinson_attribution(pw, bw, pr, br, gm)
        assert abs(result.reconciliation_residual) < TOLERANCE, (
            f"Reconciliation residual {result.reconciliation_residual} exceeds tolerance"
        )

    @pytest.mark.xfail(reason="brinson_attribution pending Phase 3 implementation")
    def test_active_return(self, portfolio_a_inputs, portfolio_a_expected):
        pw, bw, pr, br, gm = portfolio_a_inputs
        result = brinson_attribution(pw, bw, pr, br, gm)
        assert abs(result.active_return - portfolio_a_expected["active_return"]) < TOLERANCE


# ---------------------------------------------------------------------------
# Portfolio B — Pure Allocation Effect
# ---------------------------------------------------------------------------
#
# Setup:
#   Two sectors: Growth (G), Defensive (D)
#   Within-sector weights IDENTICAL in portfolio and benchmark.
#   Sector weights differ: portfolio overweights Growth (high return).
#
#   Securities and sector membership:
#     GROW_A, GROW_B → Growth
#     DEF_A, DEF_B   → Defensive
#
#   Within-sector weights (identical for portfolio and benchmark):
#     Growth:    GROW_A=0.5, GROW_B=0.5
#     Defensive: DEF_A=0.5,  DEF_B=0.5
#
#   Sector weights:
#     Portfolio:  Growth=0.7, Defensive=0.3
#     Benchmark:  Growth=0.5, Defensive=0.5
#
#   Returns:
#     GROW_A=0.12, GROW_B=0.08  → sector return = 0.10
#     DEF_A=0.03,  DEF_B=0.01  → sector return = 0.02
#
# Computed expected values:
#
#   Benchmark total return: 0.5*0.10 + 0.5*0.02 = 0.06
#   Portfolio total return: 0.7*0.10 + 0.3*0.02 = 0.076
#   Active return: 0.076 - 0.06 = 0.016
#
#   Allocation effect (BF: relative to benchmark total):
#     Growth:    (0.7 - 0.5) * (0.10 - 0.06) = 0.2 * 0.04 = 0.008
#     Defensive: (0.3 - 0.5) * (0.02 - 0.06) = -0.2 * -0.04 = 0.008
#     Total allocation: 0.016
#
#   Selection effect:
#     Growth:    0.5 * (0.10 - 0.10) = 0.0
#     Defensive: 0.5 * (0.02 - 0.02) = 0.0
#     Total selection: 0.0
#
#   Interaction effect:
#     Growth:    (0.7 - 0.5) * (0.10 - 0.10) = 0.0
#     Defensive: (0.3 - 0.5) * (0.02 - 0.02) = 0.0
#     Total interaction: 0.0
#
#   Check: total allocation = 0.016 ✓ matches active return


@pytest.fixture
def portfolio_b_inputs():
    """Inputs for Portfolio B (pure allocation)."""
    tickers = ["GROW_A", "GROW_B", "DEF_A", "DEF_B"]

    portfolio_weights = pd.Series(
        [0.7 * 0.5, 0.7 * 0.5, 0.3 * 0.5, 0.3 * 0.5],
        index=tickers,
    )  # [0.35, 0.35, 0.15, 0.15]

    benchmark_weights = pd.Series(
        [0.5 * 0.5, 0.5 * 0.5, 0.5 * 0.5, 0.5 * 0.5],
        index=tickers,
    )  # [0.25, 0.25, 0.25, 0.25]

    returns = pd.Series(
        [0.12, 0.08, 0.03, 0.01],
        index=tickers,
    )

    group_map = pd.Series(
        ["Growth", "Growth", "Defensive", "Defensive"],
        index=tickers,
    )

    return portfolio_weights, benchmark_weights, returns, returns, group_map


@pytest.fixture
def portfolio_b_expected():
    """Expected attribution output for Portfolio B."""
    return {
        "total_allocation": 0.016,
        "total_selection": 0.0,
        "total_interaction": 0.0,
        "active_return": 0.016,
        "allocation_by_sector": {"Growth": 0.008, "Defensive": 0.008},
        "selection_by_sector": {"Growth": 0.0, "Defensive": 0.0},
        "interaction_by_sector": {"Growth": 0.0, "Defensive": 0.0},
    }


class TestPortfolioB:
    """Portfolio B: pure allocation effect — no selection or interaction."""

    @pytest.mark.xfail(reason="brinson_attribution pending Phase 3 implementation")
    def test_total_allocation_effect(self, portfolio_b_inputs, portfolio_b_expected):
        pw, bw, pr, br, gm = portfolio_b_inputs
        result = brinson_attribution(pw, bw, pr, br, gm)
        assert abs(result.total_allocation - portfolio_b_expected["total_allocation"]) < TOLERANCE

    @pytest.mark.xfail(reason="brinson_attribution pending Phase 3 implementation")
    def test_selection_is_zero(self, portfolio_b_inputs, portfolio_b_expected):
        pw, bw, pr, br, gm = portfolio_b_inputs
        result = brinson_attribution(pw, bw, pr, br, gm)
        assert abs(result.total_selection - portfolio_b_expected["total_selection"]) < TOLERANCE

    @pytest.mark.xfail(reason="brinson_attribution pending Phase 3 implementation")
    def test_interaction_is_zero(self, portfolio_b_inputs, portfolio_b_expected):
        pw, bw, pr, br, gm = portfolio_b_inputs
        result = brinson_attribution(pw, bw, pr, br, gm)
        assert abs(result.total_interaction - portfolio_b_expected["total_interaction"]) < TOLERANCE

    @pytest.mark.xfail(reason="brinson_attribution pending Phase 3 implementation")
    def test_allocation_by_sector(self, portfolio_b_inputs, portfolio_b_expected):
        pw, bw, pr, br, gm = portfolio_b_inputs
        result = brinson_attribution(pw, bw, pr, br, gm)
        expected_alloc = portfolio_b_expected["allocation_by_sector"]
        for sector, expected_val in expected_alloc.items():
            assert abs(result.allocation[sector] - expected_val) < TOLERANCE, (
                f"Allocation effect for {sector}: got {result.allocation[sector]}, "
                f"expected {expected_val}"
            )

    @pytest.mark.xfail(reason="brinson_attribution pending Phase 3 implementation")
    def test_reconciliation(self, portfolio_b_inputs):
        pw, bw, pr, br, gm = portfolio_b_inputs
        result = brinson_attribution(pw, bw, pr, br, gm)
        assert abs(result.reconciliation_residual) < TOLERANCE

    @pytest.mark.xfail(reason="brinson_attribution pending Phase 3 implementation")
    def test_active_return(self, portfolio_b_inputs, portfolio_b_expected):
        pw, bw, pr, br, gm = portfolio_b_inputs
        result = brinson_attribution(pw, bw, pr, br, gm)
        assert abs(result.active_return - portfolio_b_expected["active_return"]) < TOLERANCE


# ---------------------------------------------------------------------------
# Portfolio C — Combined Effects
# ---------------------------------------------------------------------------
#
# Setup:
#   Three sectors: Tech (T), Energy (E), Utilities (U)
#   Both sector weights AND within-sector holdings differ.
#
#   Securities:
#     TECH_1, TECH_2 → Tech
#     ENRG_1, ENRG_2 → Energy
#     UTIL_1, UTIL_2 → Utilities
#
#   Returns:
#     TECH_1=0.15, TECH_2=0.05
#     ENRG_1=0.08, ENRG_2=0.04
#     UTIL_1=0.03, UTIL_2=0.01
#
#   Portfolio weights:  [0.40, 0.10, 0.20, 0.15, 0.10, 0.05]
#   Benchmark weights:  [0.25, 0.25, 0.20, 0.10, 0.10, 0.10]
#
#   Sector weights derived:
#     Portfolio:  Tech=0.50, Energy=0.35, Utilities=0.15
#     Benchmark:  Tech=0.50, Energy=0.30, Utilities=0.20
#
#   Within-sector returns:
#     Tech portfolio:    0.40/0.50 * 0.15 + 0.10/0.50 * 0.05 = 0.80*0.15 + 0.20*0.05 = 0.13
#     Tech benchmark:    0.25/0.50 * 0.15 + 0.25/0.50 * 0.05 = 0.50*0.15 + 0.50*0.05 = 0.10
#     Energy portfolio:  0.20/0.35 * 0.08 + 0.15/0.35 * 0.04 ≈ 0.5714*0.08 + 0.4286*0.04 ≈ 0.0629
#     Energy benchmark:  0.20/0.30 * 0.08 + 0.10/0.30 * 0.04 ≈ 0.6667*0.08 + 0.3333*0.04 ≈ 0.0667
#     Util portfolio:    0.10/0.15 * 0.03 + 0.05/0.15 * 0.01 = 0.6667*0.03 + 0.3333*0.01 ≈ 0.0233
#     Util benchmark:    0.10/0.20 * 0.03 + 0.10/0.20 * 0.01 = 0.50*0.03 + 0.50*0.01 = 0.02
#
#   Benchmark sector returns:
#     Tech:       0.10
#     Energy:     0.0667
#     Utilities:  0.02
#
#   Portfolio sector returns:
#     Tech:       0.13
#     Energy:     0.0629
#     Utilities:  0.0233
#
#   Benchmark total return: 0.50*0.10 + 0.30*0.0667 + 0.20*0.02
#                         = 0.05 + 0.02 + 0.004 = 0.074
#   Portfolio total return: 0.50*0.13 + 0.35*0.0629 + 0.15*0.0233
#                         = 0.065 + 0.022015 + 0.003495 = 0.09051
#   Active return:  0.09051 - 0.074 = 0.01651
#
#   Purpose of Portfolio C is RECONCILIATION — the exact values are computed
#   analytically and the test checks that all three effects sum to the active
#   return within TOLERANCE, regardless of the individual component values.
#
# NOTE: The expected values below are rounded. The implementation must produce
# values consistent with the full-precision calculation, not these rounded values.
# The definitive test is reconciliation, not matching these rounded figures.


@pytest.fixture
def portfolio_c_inputs():
    """Inputs for Portfolio C (combined allocation + selection + interaction)."""
    tickers = ["TECH_1", "TECH_2", "ENRG_1", "ENRG_2", "UTIL_1", "UTIL_2"]

    portfolio_weights = pd.Series(
        [0.40, 0.10, 0.20, 0.15, 0.10, 0.05],
        index=tickers,
    )

    benchmark_weights = pd.Series(
        [0.25, 0.25, 0.20, 0.10, 0.10, 0.10],
        index=tickers,
    )

    returns = pd.Series(
        [0.15, 0.05, 0.08, 0.04, 0.03, 0.01],
        index=tickers,
    )

    group_map = pd.Series(
        ["Tech", "Tech", "Energy", "Energy", "Utilities", "Utilities"],
        index=tickers,
    )

    return portfolio_weights, benchmark_weights, returns, returns, group_map


class TestPortfolioC:
    """Portfolio C: combined effects — primary test is arithmetic reconciliation."""

    @pytest.mark.xfail(reason="brinson_attribution pending Phase 3 implementation")
    def test_reconciliation(self, portfolio_c_inputs):
        """Allocation + selection + interaction must equal active return."""
        pw, bw, pr, br, gm = portfolio_c_inputs
        result = brinson_attribution(pw, bw, pr, br, gm)
        assert abs(result.reconciliation_residual) < TOLERANCE, (
            f"Reconciliation failed. Residual: {result.reconciliation_residual}. "
            f"Active return: {result.active_return}, "
            f"Alloc: {result.total_allocation}, Sel: {result.total_selection}, "
            f"Inter: {result.total_interaction}"
        )

    @pytest.mark.xfail(reason="brinson_attribution pending Phase 3 implementation")
    def test_active_return_sign(self, portfolio_c_inputs):
        """Portfolio C was constructed to have positive active return."""
        pw, bw, pr, br, gm = portfolio_c_inputs
        result = brinson_attribution(pw, bw, pr, br, gm)
        assert result.active_return > 0, (
            f"Expected positive active return, got {result.active_return}"
        )

    @pytest.mark.xfail(reason="brinson_attribution pending Phase 3 implementation")
    def test_result_type(self, portfolio_c_inputs):
        """Result must be a BrinsonResult instance."""
        pw, bw, pr, br, gm = portfolio_c_inputs
        result = brinson_attribution(pw, bw, pr, br, gm)
        assert isinstance(result, BrinsonResult)

    @pytest.mark.xfail(reason="brinson_attribution pending Phase 3 implementation")
    def test_sector_series_completeness(self, portfolio_c_inputs):
        """Attribution series must cover all three sectors."""
        pw, bw, pr, br, gm = portfolio_c_inputs
        result = brinson_attribution(pw, bw, pr, br, gm)
        expected_sectors = {"Tech", "Energy", "Utilities"}
        assert set(result.allocation.index) == expected_sectors
        assert set(result.selection.index) == expected_sectors
        assert set(result.interaction.index) == expected_sectors


# ---------------------------------------------------------------------------
# Structural / Interface Tests
# ---------------------------------------------------------------------------


class TestBrinsonInterface:
    """Structural checks on the BrinsonResult interface."""

    @pytest.mark.xfail(reason="brinson_attribution pending Phase 3 implementation")
    def test_result_has_required_fields(self, portfolio_a_inputs):
        pw, bw, pr, br, gm = portfolio_a_inputs
        result = brinson_attribution(pw, bw, pr, br, gm)
        # All required BrinsonResult fields must be present
        assert hasattr(result, "allocation")
        assert hasattr(result, "selection")
        assert hasattr(result, "interaction")
        assert hasattr(result, "total_allocation")
        assert hasattr(result, "total_selection")
        assert hasattr(result, "total_interaction")
        assert hasattr(result, "active_return")
        assert hasattr(result, "reconciliation_residual")

    @pytest.mark.xfail(reason="brinson_attribution pending Phase 3 implementation")
    def test_series_sum_matches_totals(self, portfolio_a_inputs):
        """Sum of per-sector series must equal the corresponding total."""
        pw, bw, pr, br, gm = portfolio_a_inputs
        result = brinson_attribution(pw, bw, pr, br, gm)
        assert abs(result.allocation.sum() - result.total_allocation) < TOLERANCE
        assert abs(result.selection.sum() - result.total_selection) < TOLERANCE
        assert abs(result.interaction.sum() - result.total_interaction) < TOLERANCE
