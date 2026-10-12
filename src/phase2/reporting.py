"""
Project Parallax — Phase 2 reporting.py
Structured result output for H1, H2, and bootstrap.

Specification: v1.0 Section 11 (2026-09-23, frozen).

Output format: machine-readable JSON to:
    data/phase2_h1_results.json
    data/phase2_h2_results.json
    data/phase2_bootstrap_results.json
    data/phase2_robustness_results.json

All CIs reported on the logit (z) scale and back-transformed to
FIRM-share (s) scale via inv_logit.  Back-transformed CIs are
asymmetric (since inv_logit is non-linear) and are labelled
clearly in the output as share_ci_lo / share_ci_hi.

No empirical data enters this module. It only formats results that
have already been computed by the calling pipeline.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Optional

import numpy as np

from .transform import inv_logit
from .bai_perron import BaiPerronResult
from .bootstrap import BootstrapResult
from .h2_system import H2Result, WaldResult


# ---------------------------------------------------------------------------
# JSON serialisation helpers
# ---------------------------------------------------------------------------

def _sanitize_nonfinite(obj):
    """
    Recursively replace all non-finite numeric values with None.

    Policy (v1.0 adjudication 2026-10-03):
        float("nan"), np.float64(nan), np.float32(nan), +inf, -inf → null

    Applied before json.dump so non-finite values never reach the encoder path.
    Python float("nan") and np.float64(nan) both inherit from Python float and
    are handled by json's native encoder as invalid JSON "NaN"; the sanitiser
    catches them here before that path is taken.
    """
    if isinstance(obj, float) and not math.isfinite(obj):
        return None
    if isinstance(obj, np.floating) and not np.isfinite(obj):
        return None
    if isinstance(obj, np.ndarray):
        # .ravel().tolist() converts np scalars to Python native types;
        # non-finite values then match the float branch above.
        return [_sanitize_nonfinite(v) for v in obj.ravel().tolist()]
    if isinstance(obj, dict):
        return {k: _sanitize_nonfinite(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize_nonfinite(v) for v in obj]
    return obj


class _NumpyEncoder(json.JSONEncoder):
    """Convert numpy scalars / arrays to plain Python types for JSON.

    Non-finite values (nan, inf, -inf) are handled by _sanitize_nonfinite
    before this encoder is invoked; allow_nan=False in _write_json catches
    any that slip through.  The ndarray branch here additionally guards
    inf/nan in case _NumpyEncoder is used directly outside _write_json.
    """

    def default(self, obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return None if not np.isfinite(obj) else float(obj)
        if isinstance(obj, np.ndarray):
            # .ravel().tolist() converts to Python floats; non-finite → None.
            return [
                (None if not math.isfinite(v) else float(v))
                for v in obj.ravel().tolist()
            ]
        return super().default(obj)


def _write_json(path: Path, data: dict, indent: int = 2) -> None:
    """Write data to path as pretty JSON, creating parent dirs as needed.

    Calls _sanitize_nonfinite first so that float("nan"), np.float64(nan),
    np.float32(nan), +inf, and -inf all serialise as JSON null.
    allow_nan=False makes json.dump raise on any residual non-finite value
    rather than silently emitting invalid JSON.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    clean = _sanitize_nonfinite(data)
    with open(path, "w") as f:
        json.dump(clean, f, cls=_NumpyEncoder, indent=indent, allow_nan=False)


# ---------------------------------------------------------------------------
# H1 result formatter
# ---------------------------------------------------------------------------

def format_h1_result(
    bp_result: BaiPerronResult,
    hac_long_run_variances: list[float],
    provenance_sha: Optional[str] = None,
) -> dict:
    """
    Format BaiPerronResult and H1 HAC estimates into JSON-ready dict.

    Parameters
    ----------
    bp_result : BaiPerronResult from run_bai_perron.
    hac_long_run_variances : list of per-segment H1 HAC long-run variance
                             estimates (length = n_breaks + 1).
    provenance_sha : SHA-256 of the input CSV (filled from config/phase2_spec.toml).

    Returns
    -------
    dict suitable for json.dumps.
    """
    # Back-transform segment means from logit to share scale.
    # Estimand: inv_logit(mean(z_t)) per segment — NOT mean(s_t) within segment.
    # These differ by Jensen's inequality; the logit-scale mean is the
    # preregistered inferential estimand (v1.0 §11 adjudication 2026-10-03).
    segment_means_z = bp_result.segment_means
    segment_means_s = [float(inv_logit(m)) for m in segment_means_z]

    # Break dates are observation indices, not z-values — no transform needed.

    return {
        "analysis": "H1",
        "description": "Bai-Perron structural break detection on logit FIRM share (z_t)",
        "spec_version": "v1.0",
        "provenance_sha256": provenance_sha,

        "n_breaks": bp_result.n_breaks,
        "break_dates_1indexed": bp_result.break_dates,
        "break_date_cis_1indexed": [
            {"lo": lo, "hi": hi}
            for lo, hi in bp_result.break_date_cis
        ],
        "break_date_ci_method": "analytic_bai_perron_asymptotic",

        "segment_means_z": segment_means_z,
        "segment_means_s": segment_means_s,
        "segment_means_s_note": (
            "inv_logit(segment_mean_z); estimand is the back-transformed logit-scale "
            "mean, not mean(s_t) within segment — these differ by Jensen's inequality"
        ),
        "segment_lengths": bp_result.segment_lengths,

        "udmax_pvalue": bp_result.udmax_pvalue,
        "sequential_pvalues": bp_result.sequential_pvalues,
        "alpha_udmax": 0.05,
        "alpha_seq": 0.05,

        "h1_hac_long_run_variances": hac_long_run_variances,
        "h1_hac_method": "Andrews_QS_AR1_prewhitened",

        "notes": bp_result.notes,
        "r_output_excerpt": bp_result.r_output[:500] if bp_result.r_output else "",
    }


def write_h1_results(
    bp_result: BaiPerronResult,
    hac_long_run_variances: list[float],
    output_path: str | Path,
    provenance_sha: Optional[str] = None,
) -> None:
    """Write H1 results JSON to output_path."""
    d = format_h1_result(bp_result, hac_long_run_variances, provenance_sha)
    _write_json(Path(output_path), d)


# ---------------------------------------------------------------------------
# Bootstrap result formatter
# ---------------------------------------------------------------------------

def format_bootstrap_result(bs_result: BootstrapResult) -> dict:
    """
    Format BootstrapResult into JSON-ready dict.

    Three distinct estimands (v1.0 §4):
    (A) Model-selection frequency table — break_count_frequency
    (B) Break-date uncertainty — analytic (NOT bootstrap)
    (C) Break-magnitude uncertainty — conditional CBB segment-mean CIs
    """
    return {
        "analysis": "H1_bootstrap",
        "spec_version": "v1.0",
        "description": "CBB bootstrap for H1 model-selection and break-magnitude uncertainty",

        "bootstrap_params": {
            "B": bs_result.total_replicates,
            "seed_used": bs_result.seed_used,
            "comparable_replicates": bs_result.comparable_replicates,
        },

        # (A) Model-selection uncertainty
        "break_count_frequency": {
            str(k): v for k, v in bs_result.break_count_frequency.items()
        },
        "break_count_frequency_pct": {
            str(k): round(100.0 * v / bs_result.total_replicates, 2)
            for k, v in bs_result.break_count_frequency.items()
        },

        # (B) Break-date uncertainty (analytic, not bootstrap)
        "break_date_ci_method": bs_result.break_date_method,

        # (C) Break-magnitude uncertainty (conditional CBB)
        "segment_mean_cis_z": [
            {"lo": lo, "hi": hi}
            for lo, hi in bs_result.segment_mean_cis
        ],
        "segment_mean_cis_s": [
            {"lo": float(inv_logit(lo)), "hi": float(inv_logit(hi))}
            for lo, hi in bs_result.segment_mean_cis
        ],
        "segment_mean_cis_s_note": (
            "inv_logit applied to z-scale CI bounds; asymmetric in share space "
            "because inv_logit is nonlinear — not a CI on mean(s_t)"
        ),

        "status": bs_result.status,
        "notes": bs_result.notes,
    }


def write_bootstrap_results(
    bs_result: BootstrapResult,
    output_path: str | Path,
) -> None:
    """Write bootstrap results JSON to output_path."""
    d = format_bootstrap_result(bs_result)
    _write_json(Path(output_path), d)


# ---------------------------------------------------------------------------
# H2 result formatter
# ---------------------------------------------------------------------------

def format_wald_result(wr: WaldResult) -> dict:
    """Format WaldResult into a JSON-ready dict."""
    return {
        "status": wr.status,
        "n_breaks": wr.n_breaks,
        "G_prime": wr.G_prime,
        "wald_stat": wr.wald_stat,
        "df": wr.df,
        "critical_value": wr.critical_value,
        "reject_h0": wr.reject_h0,
        "hac_bandwidth": wr.hac_bandwidth,
        "kappa_M": wr.kappa_M,
        "kappa_threshold": 1.0e8,
        "eigenvalues_M": (
            wr.eigenvalues_M.tolist()
            if wr.eigenvalues_M is not None else None
        ),
        "eigenvalues_Sigma": (
            wr.eigenvalues_Sigma.tolist()
            if wr.eigenvalues_Sigma is not None else None
        ),
        "nonmissing_sector_month_counts": wr.nonmissing_sector_month_counts,
    }


def format_h2_result(h2_result: H2Result) -> dict:
    """Format H2Result into JSON-ready dict."""
    d = {
        "analysis": "H2",
        "spec_version": "v1.0",
        "description": (
            "Score-based Wald test for sector heterogeneity of FIRM-share structural break"
        ),
        "status": h2_result.status,
        "G_prime": h2_result.G_prime,
        "n_breaks": h2_result.n_breaks,
        "notes": h2_result.notes,
        "nonmissing_counts": h2_result.nonmissing_counts,
    }
    if h2_result.wald is not None:
        d["wald"] = format_wald_result(h2_result.wald)
    else:
        d["wald"] = None
    return d


def write_h2_results(
    h2_result: H2Result,
    output_path: str | Path,
) -> None:
    """Write H2 results JSON to output_path."""
    d = format_h2_result(h2_result)
    _write_json(Path(output_path), d)


# ---------------------------------------------------------------------------
# Robustness result formatter
# ---------------------------------------------------------------------------

def format_robustness_result(
    raw_share_bp: BaiPerronResult,
    raw_share_bootstrap: Optional[BootstrapResult],
    raw_share_h2: Optional[H2Result],
    label: str = "raw_share_sensitivity",
) -> dict:
    """
    Format raw-share sensitivity results (SEED+2 stream, v1.0 Section 5).

    This is the same pipeline as the primary analysis but using the
    raw FIRM share s_t instead of z_t = logit(s_t).
    """
    d = {
        "analysis": "robustness",
        "label": label,
        "spec_version": "v1.0",
        "description": "Raw FIRM-share sensitivity (s_t, not logit): SEED+2 stream",
        "h1": format_h1_result(raw_share_bp, [], provenance_sha=None)
        if raw_share_bp else None,
    }
    if raw_share_bootstrap:
        d["bootstrap"] = format_bootstrap_result(raw_share_bootstrap)
    if raw_share_h2:
        d["h2"] = format_h2_result(raw_share_h2)
    return d


def write_robustness_results(
    raw_share_bp: BaiPerronResult,
    output_path: str | Path,
    raw_share_bootstrap: Optional[BootstrapResult] = None,
    raw_share_h2: Optional[H2Result] = None,
    label: str = "raw_share_sensitivity",
) -> None:
    """Write robustness results JSON to output_path."""
    d = format_robustness_result(raw_share_bp, raw_share_bootstrap, raw_share_h2, label)
    _write_json(Path(output_path), d)


# ---------------------------------------------------------------------------
# Combined summary formatter
# ---------------------------------------------------------------------------

def write_phase2_summary(
    h1_dict: dict,
    bootstrap_dict: dict,
    h2_dict: dict,
    robustness_dict: Optional[dict],
    output_path: str | Path,
    run_metadata: Optional[dict] = None,
) -> None:
    """
    Write a single combined JSON summary of all Phase 2 results.

    Parameters
    ----------
    h1_dict, bootstrap_dict, h2_dict, robustness_dict : result dicts from
        the format_* functions above.
    output_path : path to write.
    run_metadata : optional dict with run timestamp, provenance_sha, etc.
    """
    summary = {
        "phase": "Phase 2",
        "spec_version": "v1.0",
        "run_metadata": run_metadata or {},
        "h1": h1_dict,
        "bootstrap": bootstrap_dict,
        "h2": h2_dict,
        "robustness": robustness_dict,
    }
    _write_json(Path(output_path), summary)
