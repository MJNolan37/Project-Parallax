"""
Project Parallax — Brinson Attribution Engine
==============================================

Implements holdings-based Brinson-Fachler portfolio attribution.

Brinson attribution decomposes active portfolio return (portfolio return
minus benchmark return) into three components:

    Allocation effect
        The contribution to active return from overweighting or underweighting
        groups (sectors, industries) relative to the benchmark.
        Depends on: group weight differences and benchmark group returns.

    Selection effect
        The contribution to active return from holding securities within a
        group that returned differently than the group benchmark.
        Depends on: within-group security choices and benchmark group return.

    Interaction effect
        The joint effect of allocation and selection decisions within each group.
        Its treatment varies by methodology (Brinson-Hood-Beebower vs.
        Brinson-Fachler). This implementation documents the chosen convention.

Important: the Brinson selection effect is a portfolio attribution construct.
A positive selection effect does not establish that the return was idiosyncratic.
Securities may outperform their group benchmark because they carry different
systematic factor exposures. See src/attribution/factors.py for the
systematic counterpart. See tests/test_brinson.py for known-answer validation.

References
----------
Brinson, G. P., Hood, L. R., & Beebower, G. L. (1986).
    Determinants of Portfolio Performance. Financial Analysts Journal, 42(4).

Brinson, G. P., & Fachler, N. (1985).
    Measuring Non-US Equity Portfolio Performance.
    Journal of Portfolio Management, 11(3).

Notes
-----
Implementation is pending Phase 3 (Brinson Attribution Engine).
Stubs document the intended interface and validation requirements.
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Optional


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class BrinsonResult:
    """Output of a single-period Brinson attribution calculation.

    Attributes
    ----------
    allocation : pd.Series
        Allocation effect by group (sector or industry).
    selection : pd.Series
        Selection effect by group.
    interaction : pd.Series
        Interaction effect by group.
    total_allocation : float
        Sum of allocation effects across all groups.
    total_selection : float
        Sum of selection effects across all groups.
    total_interaction : float
        Sum of interaction effects across all groups.
    active_return : float
        Total portfolio active return (portfolio - benchmark).
    reconciliation_residual : float
        Difference between active return and sum of attribution effects.
        Should be near zero. Non-zero values indicate calculation errors.
    period : Optional[str]
        The period this attribution covers (e.g., "2023-Q1").
    """
    allocation: pd.Series
    selection: pd.Series
    interaction: pd.Series
    total_allocation: float
    total_selection: float
    total_interaction: float
    active_return: float
    reconciliation_residual: float
    period: Optional[str] = None


# ---------------------------------------------------------------------------
# Core attribution functions (stubs)
# ---------------------------------------------------------------------------

def brinson_attribution(
    portfolio_weights: pd.Series,
    benchmark_weights: pd.Series,
    portfolio_returns: pd.Series,
    benchmark_returns: pd.Series,
    group_map: pd.Series,
) -> BrinsonResult:
    """Compute single-period Brinson-Fachler attribution.

    Parameters
    ----------
    portfolio_weights : pd.Series
        Portfolio security weights, indexed by ticker. Must sum to 1.0.
    benchmark_weights : pd.Series
        Benchmark security weights, indexed by ticker. Must sum to 1.0.
    portfolio_returns : pd.Series
        Security returns for the period, indexed by ticker.
    benchmark_returns : pd.Series
        Same as portfolio_returns for benchmark securities.
    group_map : pd.Series
        Mapping from ticker to group (sector or industry), indexed by ticker.

    Returns
    -------
    BrinsonResult
        Attribution decomposition with reconciliation check.

    Notes
    -----
    Implementation pending Phase 3. This stub documents the intended interface.

    Validation requirement: before applying to empirical portfolios, this
    function must pass all tests in tests/test_brinson.py including the
    known-answer synthetic portfolio cases.
    """
    raise NotImplementedError(
        "brinson_attribution is pending Phase 3 implementation. "
        "See PROJECT_CHARTER.md Section 9 for validation requirements."
    )


def rolling_brinson(
    portfolio_weights: pd.DataFrame,
    benchmark_weights: pd.DataFrame,
    portfolio_returns: pd.DataFrame,
    benchmark_returns: pd.DataFrame,
    group_map: pd.DataFrame,
    frequency: str = "M",
) -> list[BrinsonResult]:
    """Compute Brinson attribution across rolling periods.

    Parameters
    ----------
    portfolio_weights : pd.DataFrame
        Time-indexed portfolio weights. Columns are tickers.
    benchmark_weights : pd.DataFrame
        Time-indexed benchmark weights. Columns are tickers.
    portfolio_returns : pd.DataFrame
        Time-indexed security returns. Columns are tickers.
    benchmark_returns : pd.DataFrame
        Same structure as portfolio_returns.
    group_map : pd.DataFrame
        Time-indexed group classifications. Columns are tickers.
    frequency : str
        Attribution period frequency ("M" for monthly, "Q" for quarterly).

    Returns
    -------
    list[BrinsonResult]
        Attribution result for each period.

    Notes
    -----
    Implementation pending Phase 3.
    """
    raise NotImplementedError(
        "rolling_brinson is pending Phase 3 implementation."
    )
