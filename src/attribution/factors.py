"""
Project Parallax — Factor Attribution Engine (FF6 Baseline)
============================================================

Implements systematic factor attribution using the Fama-French
Five-Factor Model extended with Momentum (FF6 baseline).

Factors
-------
    Mkt-RF  Market excess return (market factor)
    SMB     Small minus big (size)
    HML     High minus low (value)
    RMW     Robust minus weak (profitability)
    CMA     Conservative minus aggressive (investment)
    Mom     Momentum (UMD — up minus down)

Source: Kenneth French Data Library
    https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html

Design Principle
----------------
The FF6 model is the public, reproducible baseline for this project. It is
not declared to be a complete or definitive model of security returns. The
residual from this model — the portion of return not explained by FF6
exposures — is the primary measure of H1 (see PROJECT_CHARTER.md Section 4).

The FF6 baseline will not be upgraded opportunistically. Additional factors
require a documented research reason.

Relationship to Brinson Attribution
------------------------------------
Factor attribution and Brinson attribution answer different questions.

Brinson attribution: where in the portfolio hierarchy does active return
    appear (allocation vs. security selection within groups)?

Factor attribution: how much of a security's return is explained by
    known systematic risk exposures?

A rising Brinson selection effect that is largely explained by factor
attribution is evidence for Explanation B (classification failure) rather
than H1 (genuine idiosyncratic divergence). A rising Brinson selection
effect accompanied by rising residual variance is stronger evidence for H1.

Notes
-----
Implementation is pending Phase 4 (Factor Attribution Engine).
Stubs document the intended interface and design rationale.
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Optional


# FF6 factor names as used in the Kenneth French data files
FF6_FACTORS = ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "Mom"]


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class FactorAttributionResult:
    """Output of a factor attribution calculation for one security or portfolio.

    Attributes
    ----------
    factor_exposures : pd.Series
        Estimated beta (exposure) to each FF6 factor. Index: factor names.
    factor_contributions : pd.Series
        Return contribution from each factor (exposure × factor return).
    explained_return : float
        Total return explained by the factor model.
    residual_return : float
        Return not explained by the factor model.
    total_return : float
        Total security or portfolio return for the period.
    r_squared : float
        Coefficient of determination for the factor regression.
    residual_variance : float
        Variance of residual returns.
    total_variance : float
        Total return variance.
    specific_variance_share : float
        residual_variance / total_variance. Primary measure for H1 testing.
    """
    factor_exposures: pd.Series
    factor_contributions: pd.Series
    explained_return: float
    residual_return: float
    total_return: float
    r_squared: float
    residual_variance: float
    total_variance: float
    specific_variance_share: float


# ---------------------------------------------------------------------------
# Factor data retrieval (stub)
# ---------------------------------------------------------------------------

def load_ff6_factors(
    start_date: str,
    end_date: str,
    frequency: str = "monthly",
    cache_path: Optional[str] = None,
) -> pd.DataFrame:
    """Load Fama-French FF6 factor returns from the French Data Library.

    Parameters
    ----------
    start_date : str
        Start date for factor data (YYYY-MM-DD).
    end_date : str
        End date for factor data (YYYY-MM-DD).
    frequency : str
        "monthly" or "daily". Monthly data is the primary baseline.
    cache_path : str, optional
        If provided, cache the downloaded data at this path to avoid
        repeated downloads.

    Returns
    -------
    pd.DataFrame
        Factor returns indexed by date. Columns: Mkt-RF, SMB, HML, RMW, CMA, Mom.
        Values are decimal returns (not percentages).

    Notes
    -----
    Implementation pending Phase 4.
    """
    raise NotImplementedError(
        "load_ff6_factors is pending Phase 4 implementation."
    )


# ---------------------------------------------------------------------------
# Core attribution functions (stubs)
# ---------------------------------------------------------------------------

def estimate_factor_exposures(
    security_returns: pd.Series,
    factor_returns: pd.DataFrame,
    window: Optional[int] = None,
    min_periods: int = 24,
) -> pd.Series:
    """Estimate FF6 factor exposures via OLS regression.

    Parameters
    ----------
    security_returns : pd.Series
        Time series of security excess returns (return minus risk-free rate).
    factor_returns : pd.DataFrame
        FF6 factor returns aligned to the same index. Columns: FF6_FACTORS.
    window : int, optional
        If provided, estimate over a rolling window of this many periods.
        If None, estimate over the full sample.
    min_periods : int
        Minimum number of observations required for estimation.

    Returns
    -------
    pd.Series
        Estimated factor exposures (betas). Index: FF6_FACTORS.
        Includes alpha (intercept) as "Alpha".

    Notes
    -----
    Implementation pending Phase 4.
    """
    raise NotImplementedError(
        "estimate_factor_exposures is pending Phase 4 implementation."
    )


def factor_attribution(
    security_returns: pd.Series,
    factor_returns: pd.DataFrame,
    exposures: Optional[pd.Series] = None,
) -> FactorAttributionResult:
    """Decompose security return into systematic and specific components.

    Parameters
    ----------
    security_returns : pd.Series
        Security return time series.
    factor_returns : pd.DataFrame
        FF6 factor returns aligned to the same index.
    exposures : pd.Series, optional
        Pre-estimated factor exposures. If None, estimated from the data.

    Returns
    -------
    FactorAttributionResult
        Full factor decomposition including residual and specific variance share.

    Notes
    -----
    Implementation pending Phase 4.

    The specific_variance_share in the result is the primary measure of H1.
    See PROJECT_CHARTER.md Section 4.1 and Section 6 for the operationalization.
    """
    raise NotImplementedError(
        "factor_attribution is pending Phase 4 implementation."
    )


def rolling_specific_variance(
    security_returns: pd.DataFrame,
    factor_returns: pd.DataFrame,
    window: int = 36,
    min_periods: int = 24,
) -> pd.DataFrame:
    """Compute rolling specific variance share for a panel of securities.

    This is the primary time-series measure for testing H1: whether the
    share of security-level return variation not explained by systematic
    factors has increased over time.

    Parameters
    ----------
    security_returns : pd.DataFrame
        Panel of security returns. Columns are tickers, index is dates.
    factor_returns : pd.DataFrame
        FF6 factor returns aligned to the same index.
    window : int
        Rolling estimation window in periods.
    min_periods : int
        Minimum observations required for estimation.

    Returns
    -------
    pd.DataFrame
        Rolling specific variance share. Same structure as security_returns.

    Notes
    -----
    Implementation pending Phase 5 (Comparative Attribution).
    """
    raise NotImplementedError(
        "rolling_specific_variance is pending Phase 5 implementation."
    )
