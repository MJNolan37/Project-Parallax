"""
Project Parallax — Phase 2 transform.py
FIRM-share logit transformation and inverse.

Specification: v1.0 Section 2 (2026-09-23, frozen).

Design:
    z_t = log(FIRM_t / (MKT_t + IND_t))   [= logit(s_t)]

where s_t = FIRM_t / (MKT_t + IND_t + FIRM_t) is the FIRM variance share.

Boundary handling (v1.0 Section 2):
    - s_t == 0 exactly  → DataQualityError (halt)
    - s_t == 1 exactly  → DataQualityError (halt)
    - 0 < s_t < 1e-6    → cap s_t = 1e-6, record cap event, continue
    - 1-1e-6 < s_t < 1  → cap s_t = 1-1e-6, record cap event, continue
    "No extra sensitivity is triggered by a cap."
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Sequence

import numpy as np
import pandas as pd

# Boundary constants — must match config/phase2_spec.toml [transform]
BOUNDARY_LOWER: float = 1e-6
BOUNDARY_UPPER: float = 1.0 - 1e-6


class DataQualityError(ValueError):
    """Raised when FIRM share is exactly 0 or 1 (v1.0 Section 2 halt condition)."""


@dataclass
class TransformResult:
    """Output of compute_z_series."""
    z: np.ndarray                    # logit(FIRM share), length T
    s: np.ndarray                    # FIRM share (after boundary handling), length T
    dates: pd.DatetimeIndex          # aligned with z and s
    cap_events: list[dict] = field(default_factory=list)
    # Each cap event: {"date": ..., "s_raw": ..., "s_capped": ..., "side": "lower"|"upper"}


def firm_share(mkt: float | np.ndarray,
               ind: float | np.ndarray,
               firm: float | np.ndarray) -> float | np.ndarray:
    """
    Compute FIRM variance share s_t = FIRM / (MKT + IND + FIRM).

    Parameters
    ----------
    mkt, ind, firm : scalar or array of non-negative variance components.

    Returns
    -------
    s : same type/shape as inputs.
    """
    total = mkt + ind + firm
    return firm / total


def logit_share(s: float | np.ndarray) -> float | np.ndarray:
    """
    logit(s) = log(s / (1 - s)) for s in (0, 1).

    Boundary conditions (halt/cap) must be handled BEFORE calling this;
    this function does not check limits.
    """
    return np.log(s / (1.0 - s))


def inv_logit(z: float | np.ndarray) -> float | np.ndarray:
    """Inverse logit (sigmoid): s = 1 / (1 + exp(-z))."""
    return 1.0 / (1.0 + np.exp(-z))


def _apply_boundary(s_raw: float,
                    date,
                    cap_events: list[dict]) -> float:
    """
    Apply v1.0 boundary rules to a single share value.

    Parameters
    ----------
    s_raw : raw FIRM share value.
    date  : associated date (for logging).
    cap_events : mutable list; cap events appended in-place.

    Returns
    -------
    s_handled : share value after boundary treatment.

    Raises
    ------
    DataQualityError if s_raw == 0.0 or s_raw == 1.0 exactly.
    """
    if s_raw == 0.0:
        raise DataQualityError(
            f"FIRM share is exactly 0 at {date}: data quality failure. "
            "Check FIRM variance component in Phase 1 output."
        )
    if s_raw == 1.0:
        raise DataQualityError(
            f"FIRM share is exactly 1 at {date}: data quality failure. "
            "Check MKT+IND variance components in Phase 1 output."
        )

    s_out = s_raw
    if s_raw < BOUNDARY_LOWER:
        s_out = BOUNDARY_LOWER
        cap_events.append({
            "date": date,
            "s_raw": s_raw,
            "s_capped": s_out,
            "side": "lower",
        })
    elif s_raw > BOUNDARY_UPPER:
        s_out = BOUNDARY_UPPER
        cap_events.append({
            "date": date,
            "s_raw": s_raw,
            "s_capped": s_out,
            "side": "upper",
        })
    return s_out


def compute_z_series(df: pd.DataFrame,
                     mkt_col: str = "MKT",
                     ind_col: str = "IND",
                     firm_col: str = "FIRM",
                     date_col: str | None = None) -> TransformResult:
    """
    Compute z_t = logit(s_t) for a monthly CLMX decomposition DataFrame.

    Parameters
    ----------
    df : DataFrame with columns [date, MKT, IND, FIRM] (or as specified).
         Index must be DatetimeIndex or date_col must be named.
    mkt_col, ind_col, firm_col : column names.
    date_col : if None, uses df.index as dates.

    Returns
    -------
    TransformResult with z, s, dates, cap_events.

    Raises
    ------
    DataQualityError on exact 0 or 1 FIRM share (v1.0 halt condition).
    ValueError on missing columns or non-positive variance totals.
    """
    # Resolve date index
    if date_col is not None:
        dates = pd.DatetimeIndex(df[date_col])
    else:
        dates = pd.DatetimeIndex(df.index)

    mkt = df[mkt_col].to_numpy(dtype=float)
    ind = df[ind_col].to_numpy(dtype=float)
    firm = df[firm_col].to_numpy(dtype=float)

    # Validate positivity
    total = mkt + ind + firm
    if np.any(total <= 0):
        bad = np.where(total <= 0)[0]
        raise ValueError(
            f"Non-positive total variance at row(s) {bad}. "
            "CLMX components must be non-negative with positive sum."
        )

    s_raw = firm / total
    cap_events: list[dict] = []
    s_handled = np.empty_like(s_raw)

    for i, (s_i, d_i) in enumerate(zip(s_raw, dates)):
        s_handled[i] = _apply_boundary(float(s_i), d_i, cap_events)

    z = logit_share(s_handled)

    return TransformResult(z=z, s=s_handled, dates=dates, cap_events=cap_events)


def back_transform_ci(z_lo: float | np.ndarray,
                      z_hi: float | np.ndarray) -> tuple:
    """
    Back-transform a confidence interval from logit to share space.

    Parameters
    ----------
    z_lo, z_hi : lower and upper CI bounds on z = logit(s).

    Returns
    -------
    (s_lo, s_hi) : CI bounds on FIRM share s.
    """
    return inv_logit(z_lo), inv_logit(z_hi)
