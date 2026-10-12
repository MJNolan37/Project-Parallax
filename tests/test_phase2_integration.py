"""
Project Parallax — Phase 2.1 integration test
End-to-end on fully synthetic data → valid JSON output.

Specification: v1.0 (2026-09-23, frozen).

Verifies:
    1. Full pipeline from synthetic z_t → reporting.py → JSON
    2. JSON schema: all required keys present, correct types
    3. Back-transform: segment_means_s values in (0,1)
    4. H2 Wald scaling: homogeneous break W < cv (T-scaling correct)
    5. Reporting: write_h1_results, write_h2_results, write_bootstrap_results
                  write_robustness_results produce valid JSON files
    6. _NumpyEncoder handles NaN → null, numpy scalars, arrays
    7. Robustness module: synthetic raw-share, correct SEED+2 stream

No empirical data is used. No rpy2 required for most tests.
Bai-Perron JSON formatting tested with a hand-constructed BaiPerronResult.

Exit codes:
    0 : all tests passed
    1 : at least one test failed
"""

import sys, os, json, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from pathlib import Path

from src.phase2.transform import logit_share as logit, inv_logit
from src.phase2.bai_perron import BaiPerronResult
from src.phase2.bootstrap import BootstrapResult
from src.phase2.h2_system import (
    H2Result, WaldResult, run_h2, wald_test,
    CV_CHI2_11, CV_CHI2_22, N_MIN,
)
from src.phase2.reporting import (
    format_h1_result,
    format_h2_result,
    format_wald_result,
    format_bootstrap_result,
    format_robustness_result,
    write_h1_results,
    write_h2_results,
    write_bootstrap_results,
    write_robustness_results,
    write_phase2_summary,
    _NumpyEncoder,
    _sanitize_nonfinite,
    _write_json,
)
from src.phase2.robustness import (
    synthetic_raw_share,
    ROBUSTNESS_SEED,
    run_robustness_bootstrap,
)

passes = 0
fails = 0


def check(name, condition, msg=""):
    global passes, fails
    if condition:
        print(f"  PASS  {name}")
        passes += 1
    else:
        print(f"  FAIL  {name}: {msg}")
        fails += 1


# ---------------------------------------------------------------------------
# Helper: build synthetic BaiPerronResult (1 break at t=90)
# ---------------------------------------------------------------------------

def make_bp_one_break() -> BaiPerronResult:
    z1 = -0.3
    z2 = 0.8
    return BaiPerronResult(
        n_breaks=1,
        break_dates=[90],
        break_date_cis=[(67, 113)],
        segment_means=[z1, z2],
        segment_lengths=[90, 90],
        udmax_pvalue=0.003,
        sequential_pvalues=[0.001],
        r_output="[strucchange output excerpt]",
        notes=["Synthetic test result"],
    )


def make_bp_zero_breaks() -> BaiPerronResult:
    return BaiPerronResult(
        n_breaks=0,
        break_dates=[],
        break_date_cis=[],
        segment_means=[0.2],
        segment_lengths=[180],
        udmax_pvalue=0.42,
        sequential_pvalues=[],
        r_output="",
        notes=[],
    )


def make_bootstrap_result(n_breaks=1) -> BootstrapResult:
    from src.phase2.bootstrap import SEED
    return BootstrapResult(
        break_count_frequency={0: 50, 1: 1700, 2: 249},
        total_replicates=1999,
        comparable_replicates=1700,
        segment_mean_cis=[(-0.45, -0.15), (0.65, 0.95)],
        break_date_method="analytic_bai_perron",
        status="ok",
        notes=[],
        seed_used=SEED,
    )


def make_h2_ok() -> H2Result:
    wr = WaldResult(
        status="ok",
        n_breaks=1,
        G_prime=12,
        wald_stat=15.2,
        df=11,
        critical_value=CV_CHI2_11,
        reject_h0=False,
        hac_bandwidth=3.2,
        kappa_M=1234.5,
        eigenvalues_M=np.array([0.1, 0.2, 0.3]),
        eigenvalues_Sigma=np.array([0.001, 0.002]),
        nonmissing_sector_month_counts={"MFG": 180, "TECH": 178},
    )
    return H2Result(
        status="ok",
        G_prime=12,
        n_breaks=1,
        wald=wr,
        nonmissing_counts={"MFG": 180, "TECH": 178},
        notes=[],
    )


def make_h2_singular() -> H2Result:
    wr = WaldResult(
        status="singular",
        n_breaks=1,
        G_prime=12,
        wald_stat=None,
        df=11,
        critical_value=CV_CHI2_11,
        reject_h0=None,
        kappa_M=1.2e9,
        eigenvalues_M=np.array([0.0, 0.1]),
        eigenvalues_Sigma=np.array([0.0, 0.001]),
    )
    return H2Result(
        status="singular",
        G_prime=12,
        n_breaks=1,
        wald=wr,
        notes=["κ(M) = 1.2e9 > 1e8 — H2 Wald not computable"],
    )


# ---------------------------------------------------------------------------
# 1. Non-finite JSON handling: all 5 cases must serialise to null
#
#    Policy (v1.0 adjudication 2026-10-03):
#      float("nan"), np.float64(nan), np.float32(nan), +inf, -inf → null
#
#    _sanitize_nonfinite runs before json.dump in _write_json; allow_nan=False
#    makes json.dump raise on any residual non-finite value.  Tests use the
#    _write_json path (end-to-end) so that the full policy is exercised.
# ---------------------------------------------------------------------------
print("=== Non-finite JSON serialisation (all 5 cases) ===")

import math as _math

with tempfile.TemporaryDirectory() as _tmpdir_nf:
    _p_nf = Path(_tmpdir_nf)
    _nf_data = {
        "python_nan":      float("nan"),
        "np_float64_nan":  np.float64(np.nan),
        "np_float32_nan":  np.float32(np.nan),
        "pos_inf":         float("inf"),
        "neg_inf":         float("-inf"),
        "valid_float":     3.14,
        "valid_int":       np.int64(42),
        "arr_with_nan":    np.array([1.0, float("nan"), 3.0]),
    }
    _nf_path = _p_nf / "nonfinite.json"
    _write_json(_nf_path, _nf_data)
    with open(_nf_path) as _f:
        _nf_parsed = json.load(_f)

check("float('nan') → null in JSON",
      _nf_parsed["python_nan"] is None)
check("np.float64(nan) → null in JSON",
      _nf_parsed["np_float64_nan"] is None)
check("np.float32(nan) → null in JSON",
      _nf_parsed["np_float32_nan"] is None)
check("+inf → null in JSON",
      _nf_parsed["pos_inf"] is None)
check("-inf → null in JSON",
      _nf_parsed["neg_inf"] is None)
check("valid float preserved through _write_json",
      abs(_nf_parsed["valid_float"] - 3.14) < 1e-10)
check("np.int64 serialises to int",
      _nf_parsed["valid_int"] == 42)
check("ndarray with NaN: null at position 1",
      _nf_parsed["arr_with_nan"][1] is None)
check("ndarray: first element = 1.0",
      _nf_parsed["arr_with_nan"][0] == 1.0)


# ---------------------------------------------------------------------------
# 2. format_h1_result: schema and back-transform
# ---------------------------------------------------------------------------
print("\n=== format_h1_result ===")

bp = make_bp_one_break()
h1_d = format_h1_result(bp, hac_long_run_variances=[0.45, 0.38], provenance_sha="abc123")

check("analysis key = H1", h1_d["analysis"] == "H1")
check("spec_version present", h1_d.get("spec_version") == "v1.0")
check("n_breaks = 1", h1_d["n_breaks"] == 1)
check("break_dates_1indexed = [90]", h1_d["break_dates_1indexed"] == [90])
check("break_date_cis has 1 entry", len(h1_d["break_date_cis_1indexed"]) == 1)
check("break_date_ci has lo/hi keys",
      "lo" in h1_d["break_date_cis_1indexed"][0] and "hi" in h1_d["break_date_cis_1indexed"][0])
check("segment_means_z = [-0.3, 0.8]",
      abs(h1_d["segment_means_z"][0] - (-0.3)) < 1e-10 and
      abs(h1_d["segment_means_z"][1] - 0.8) < 1e-10)
check("segment_means_s in (0,1) for s[0]",
      0 < h1_d["segment_means_s"][0] < 1)
check("segment_means_s in (0,1) for s[1]",
      0 < h1_d["segment_means_s"][1] < 1)
check("back-transform correct: inv_logit(-0.3)",
      abs(h1_d["segment_means_s"][0] - float(inv_logit(-0.3))) < 1e-10)
check("provenance_sha present", h1_d["provenance_sha256"] == "abc123")
check("hac_long_run_variances present", h1_d["h1_hac_long_run_variances"] == [0.45, 0.38])
check("notes is list", isinstance(h1_d["notes"], list))

# 0-break case
h1_d0 = format_h1_result(make_bp_zero_breaks(), [])
check("0-break: n_breaks=0", h1_d0["n_breaks"] == 0)
check("0-break: one segment mean", len(h1_d0["segment_means_z"]) == 1)
check("0-break: one segment mean_s", len(h1_d0["segment_means_s"]) == 1)


# ---------------------------------------------------------------------------
# 3. format_bootstrap_result: schema
# ---------------------------------------------------------------------------
print("\n=== format_bootstrap_result ===")

bs = make_bootstrap_result()
bs_d = format_bootstrap_result(bs)

check("analysis key = H1_bootstrap", bs_d["analysis"] == "H1_bootstrap")
check("break_count_frequency present", "break_count_frequency" in bs_d)
check("frequency sum = B", sum(bs_d["break_count_frequency"].values()) == 1999)
check("break_count_frequency_pct present", "break_count_frequency_pct" in bs_d)
check("freq pct for 1-break",
      abs(bs_d["break_count_frequency_pct"]["1"] - 100.0 * 1700 / 1999) < 0.01)
check("segment_mean_cis_z has 2 entries",
      len(bs_d["segment_mean_cis_z"]) == 2)
check("segment_mean_cis_s has 2 entries",
      len(bs_d["segment_mean_cis_s"]) == 2)
check("segment_mean_cis_s values in (0,1)",
      all(0 < e["lo"] < 1 and 0 < e["hi"] < 1
          for e in bs_d["segment_mean_cis_s"]))
check("break_date_ci_method = analytic", bs_d["break_date_ci_method"] == "analytic_bai_perron")
check("comparable_replicates in bootstrap_params",
      bs_d["bootstrap_params"]["comparable_replicates"] == 1700)


# ---------------------------------------------------------------------------
# 4. format_wald_result and format_h2_result
# ---------------------------------------------------------------------------
print("\n=== format_wald_result / format_h2_result ===")

h2 = make_h2_ok()
h2_d = format_h2_result(h2)

check("analysis key = H2", h2_d["analysis"] == "H2")
check("wald sub-dict present", h2_d["wald"] is not None)
wd = h2_d["wald"]
check("wald status = ok", wd["status"] == "ok")
check("wald_stat = 15.2", abs(wd["wald_stat"] - 15.2) < 1e-10)
check("critical_value present", wd["critical_value"] == CV_CHI2_11)
check("reject_h0 = False", wd["reject_h0"] is False)
check("kappa_threshold = 1e8", wd["kappa_threshold"] == 1e8)
check("eigenvalues_M serialised as list", isinstance(wd["eigenvalues_M"], list))

# Singular case
h2_sing = make_h2_singular()
h2_sing_d = format_h2_result(h2_sing)
check("singular: status = singular", h2_sing_d["status"] == "singular")
check("singular: wald.status = singular", h2_sing_d["wald"]["status"] == "singular")
check("singular: wald_stat = null", h2_sing_d["wald"]["wald_stat"] is None)


# ---------------------------------------------------------------------------
# 5. write_* functions: produce valid JSON files
# ---------------------------------------------------------------------------
print("\n=== write_* functions produce valid JSON ===")

with tempfile.TemporaryDirectory() as tmpdir:
    p = Path(tmpdir)

    # H1
    h1_path = p / "h1.json"
    write_h1_results(bp, [0.45, 0.38], h1_path, provenance_sha="abc123")
    check("H1 JSON file exists", h1_path.exists())
    with open(h1_path) as f:
        h1_loaded = json.load(f)
    check("H1 JSON parseable and n_breaks=1", h1_loaded["n_breaks"] == 1)

    # Bootstrap
    bs_path = p / "bootstrap.json"
    write_bootstrap_results(bs, bs_path)
    check("bootstrap JSON file exists", bs_path.exists())
    with open(bs_path) as f:
        bs_loaded = json.load(f)
    check("bootstrap JSON parseable", bs_loaded["analysis"] == "H1_bootstrap")

    # H2
    h2_path = p / "h2.json"
    write_h2_results(h2, h2_path)
    check("H2 JSON file exists", h2_path.exists())
    with open(h2_path) as f:
        h2_loaded = json.load(f)
    check("H2 JSON parseable", h2_loaded["analysis"] == "H2")

    # Robustness
    rob_path = p / "robustness.json"
    write_robustness_results(make_bp_zero_breaks(), rob_path,
                             raw_share_bootstrap=None, raw_share_h2=None)
    check("robustness JSON file exists", rob_path.exists())
    with open(rob_path) as f:
        rob_loaded = json.load(f)
    check("robustness JSON parseable", rob_loaded["analysis"] == "robustness")

    # Combined summary
    summary_path = p / "summary.json"
    write_phase2_summary(
        h1_d, bs_d, h2_d,
        robustness_dict=rob_loaded,
        output_path=summary_path,
        run_metadata={"run_date": "2026-10-03"},
    )
    check("summary JSON file exists", summary_path.exists())
    with open(summary_path) as f:
        summary = json.load(f)
    check("summary has all top-level keys",
          all(k in summary for k in ("phase", "h1", "bootstrap", "h2", "robustness")))
    check("summary.h1.n_breaks = 1", summary["h1"]["n_breaks"] == 1)

    # Parent dir creation
    nested_path = p / "sub" / "dir" / "h1_nested.json"
    write_h1_results(bp, [], nested_path)
    check("write_h1_results creates parent dirs", nested_path.exists())


# ---------------------------------------------------------------------------
# 6. H2 Wald validation: regression fixture + Monte Carlo size calibration
#
#    Two separate evidential purposes:
#
#    (A) REGRESSION FIXTURE (seed=2026): detects accidental changes to the
#        Wald formula, HAC, or scoring across code revisions.  The specific
#        W value is seed-dependent and is NOT evidence that the null size is
#        correct; do not interpret W < cv here as calibration evidence.
#
#    (B) MONTE CARLO SIZE CALIBRATION: draws delta ~ N(0, Sigma_oracle) for
#        known PD Sigma_oracle = I_12 and computes the oracle Wald statistic
#        W = (R delta)'(R Sigma_oracle R')^{-1}(R delta) ~ chi²(11) exactly.
#        Counts rejections (W > CV_CHI2_11 = 19.68) over B=2000 draws and
#        checks that the empirical rejection rate is within [1%, 9%] of the
#        nominal 5%.  This is genuine size calibration evidence independent
#        of any specific data realisation.
# ---------------------------------------------------------------------------
print("\n=== H2 Wald validation: regression fixture + MC size calibration ===")

# --- (A) Regression fixture: seed=2026, one-break homogeneous scenario ---
rng_h2 = np.random.default_rng(2026)   # REGRESSION FIXTURE — seed chosen prior to code
T, G = 180, 12
eps = rng_h2.normal(0, 0.5, (T, G))
sector_z = np.zeros((T, G))
sector_z[:90, :] = -0.3
sector_z[90:, :] = 0.2
sector_z += eps
valid_mask_h2 = np.ones((T, G), dtype=bool)

r_h2 = run_h2(sector_z, valid_mask_h2, break_dates=[90])
check("regression fixture: H2 status ok", r_h2.status == "ok")
check("regression fixture: W < cv (homogeneous null, seed=2026)",
      r_h2.wald is not None and r_h2.wald.wald_stat < CV_CHI2_11,
      f"W={r_h2.wald.wald_stat:.4f}" if r_h2.wald else "wald=None")

# Heterogeneous break sanity check (regression fixture)
sector_z_het = sector_z.copy()
sector_z_het[:90, 0] = 0.5
sector_z_het[90:, 0] = -1.0
r_h2_het = run_h2(sector_z_het, valid_mask_h2, break_dates=[90])
check("regression fixture: heterogeneous break detected (W > cv)",
      r_h2_het.wald is not None and r_h2_het.wald.wald_stat > CV_CHI2_11,
      f"W={r_h2_het.wald.wald_stat:.4f}, cv={CV_CHI2_11}" if r_h2_het.wald else "None")

# --- (B) Monte Carlo size calibration: oracle Wald under H0 → chi²(11) ---
# delta ~ N(0, I_12); oracle W = (R delta)'(R R')^{-1}(R delta) ~ chi²(11)
# R R' for contrast_matrix(12): diag=2, off-diag=1 → eigenvalues {12, 1×10} → κ=12 << 1e8
print("\n=== Monte Carlo size calibration (oracle Wald, B=2000) ===")

rng_mc = np.random.default_rng(20261003)
G_mc, n_draws_mc = 12, 2000
Sigma_oracle = np.eye(G_mc)      # identity: κ(M)=12, exact chi²(11) under H0

n_reject_mc, n_ok_mc = 0, 0
for _ in range(n_draws_mc):
    delta_mc = rng_mc.multivariate_normal(np.zeros(G_mc), Sigma_oracle)
    wr_mc = wald_test(delta_mc, Sigma_oracle, G_mc, n_breaks=1)
    if wr_mc.status == "ok":
        n_ok_mc += 1
        if wr_mc.reject_h0:
            n_reject_mc += 1

mc_rate = n_reject_mc / n_ok_mc if n_ok_mc > 0 else float("nan")
# Under chi²(11) at 5% CV: expected 5% → 100/2000.
# Binomial(2000, 0.05): σ ≈ 9.7; bounds [1%, 9%] = ±4.1σ (>99.996% coverage).
check("MC size calibration: 1% ≤ rejection rate ≤ 9% of nominal 5%",
      0.01 <= mc_rate <= 0.09,
      f"rate={mc_rate:.3f} ({n_reject_mc}/{n_ok_mc} of {n_draws_mc} draws)")
check("MC: all draws computable (kappa OK for identity Sigma)",
      n_ok_mc == n_draws_mc,
      f"n_ok={n_ok_mc}/{n_draws_mc}")
print(f"  INFO  MC oracle Wald rejection rate = {mc_rate:.3f} "
      f"({n_reject_mc}/{n_ok_mc}, nominal 5%, cv={CV_CHI2_11})")


# ---------------------------------------------------------------------------
# 7. Robustness module: synthetic_raw_share and SEED constant
# ---------------------------------------------------------------------------
print("\n=== robustness module ===")

from src.phase2.bootstrap import SEED as PRIMARY_SEED

check("ROBUSTNESS_SEED = PRIMARY_SEED + 2",
      ROBUSTNESS_SEED == PRIMARY_SEED + 2)

s_syn = synthetic_raw_share(T=180, tau=90, shift=0.1, base=0.35)
check("synthetic_raw_share: length 180", len(s_syn) == 180)
check("synthetic_raw_share: all in (0,1)", np.all((s_syn > 0) & (s_syn < 1)))
check("synthetic_raw_share: visible shift",
      float(np.mean(s_syn[90:])) > float(np.mean(s_syn[:90])))

# run_robustness_bootstrap with a dummy estimator (no rpy2)
class _DummyBPResult:
    """Minimal object mimicking BaiPerronResult for bootstrap test."""
    def __init__(self, n):
        self.n_breaks = n
        self.break_dates = [90] if n == 1 else []
        self.break_date_cis = [(70, 110)] if n == 1 else []
        self.segment_means = [-0.1, 0.3] if n == 1 else [0.1]
        self.segment_lengths = [90, 90] if n == 1 else [180]
        self.udmax_pvalue = 0.01 if n == 1 else 0.4
        self.sequential_pvalues = [0.005] if n == 1 else []
        self.r_output = ""
        self.notes = []

def _dummy_estimator(s):
    """Always returns 1 break at t=90; computes actual segment means from s."""
    r = _DummyBPResult(1)
    # Compute real segment means from the resampled series so CIs are non-degenerate.
    import numpy as _np
    s_arr = _np.asarray(s)
    r.segment_means = [float(_np.mean(s_arr[:90])), float(_np.mean(s_arr[90:]))]
    return r

bs_rob = run_robustness_bootstrap(
    s_syn,
    observed_n_breaks=1,
    break_estimator=_dummy_estimator,
    n_replicates=300,     # small for speed; B=1999 in production
    seed=ROBUSTNESS_SEED,
)
check("robustness bootstrap: comparable_replicates = 300",
      bs_rob.comparable_replicates == 300)
check("robustness bootstrap: status ok", bs_rob.status == "ok")
check("robustness bootstrap: 2 segment CIs",
      len(bs_rob.segment_mean_cis) == 2)
check("robustness bootstrap: seed = ROBUSTNESS_SEED",
      bs_rob.seed_used == ROBUSTNESS_SEED)
check("robustness bootstrap: total_replicates = 300",
      bs_rob.total_replicates == 300)
check("robustness bootstrap: CI lo < hi",
      all(lo < hi for lo, hi in bs_rob.segment_mean_cis
          if not (lo != lo)))  # skip NaN pairs

# Insufficient replicates case
bs_ins = run_robustness_bootstrap(
    s_syn,
    observed_n_breaks=1,
    break_estimator=lambda s: _DummyBPResult(0),  # always returns 0 breaks
    n_replicates=300,
    seed=ROBUSTNESS_SEED,
)
check("insufficient replicates: status = insufficient_replicates",
      bs_ins.status == "insufficient_replicates")


# ---------------------------------------------------------------------------
# 8. format_robustness_result: schema
# ---------------------------------------------------------------------------
print("\n=== format_robustness_result ===")

bp_zero = make_bp_zero_breaks()
bs_rob_result = make_bootstrap_result(n_breaks=0)
bs_rob_result.segment_mean_cis = [(0.1, 0.4)]
bs_rob_result.break_count_frequency = {0: 1600, 1: 350, 2: 49}

rob_d = format_robustness_result(bp_zero, bs_rob_result, None)
check("robustness analysis key", rob_d["analysis"] == "robustness")
check("robustness description present", "description" in rob_d)
check("robustness h1.n_breaks = 0", rob_d["h1"]["n_breaks"] == 0)
check("robustness bootstrap.total_replicates = 1999",
      rob_d["bootstrap"]["bootstrap_params"]["B"] == 1999)
check("robustness h2 = None (not passed)", rob_d.get("h2") is None)


# ---------------------------------------------------------------------------
# 9. Byte-identical JSON determinism: same synthetic run → same bytes
#    Verifies that JSON output is fully deterministic: no timestamp, no
#    random state leak, no float formatting variation across two runs.
#    Both runs use identical inputs (same rng seed, same synthetic z).
# ---------------------------------------------------------------------------
print("\n=== Byte-identical JSON determinism ===")

import hashlib

def _synthetic_h2_run(seed: int, tmpdir_path: Path) -> str:
    """Run format_h2_result on a fixed synthetic input, return JSON bytes hash."""
    rng_det = np.random.default_rng(seed)
    T_det, G_det = 180, 12
    tau_det = 90
    eps_det = rng_det.normal(0, 0.5, (T_det, G_det))
    z_det = np.zeros((T_det, G_det))
    z_det[:tau_det, :] = -0.2
    z_det[tau_det:, :] = 0.3
    z_det += eps_det
    valid_det = np.ones((T_det, G_det), dtype=bool)

    r_det = run_h2(z_det, valid_det, break_dates=[tau_det])
    h2_det_d = format_h2_result(r_det)
    # Use write_h2_results for the full end-to-end path (includes json.dumps)
    out_path = tmpdir_path / f"det_run_{seed}.json"
    write_h2_results(r_det, out_path)
    raw = out_path.read_bytes()
    return hashlib.sha256(raw).hexdigest(), raw

with tempfile.TemporaryDirectory() as tmpdir_det:
    p_det = Path(tmpdir_det)
    digest_1, raw_1 = _synthetic_h2_run(20260923, p_det)
    digest_2, raw_2 = _synthetic_h2_run(20260923, p_det)

    check("H2 JSON byte-identical on repeated run",
          digest_1 == digest_2,
          f"sha256_run1={digest_1[:12]}... sha256_run2={digest_2[:12]}...")

    # Also verify that a different seed produces DIFFERENT output (sanity check)
    digest_alt, _ = _synthetic_h2_run(99999, p_det)
    check("Different seed produces different JSON (sanity)",
          digest_1 != digest_alt)

# Also verify format_h1_result is deterministic (reporting.py path)
def _h1_json_hash() -> str:
    bp_det = make_bp_one_break()
    d = format_h1_result(bp_det, hac_long_run_variances=[0.45, 0.38], provenance_sha="abc123")
    return hashlib.sha256(json.dumps(d, cls=_NumpyEncoder, indent=2).encode()).hexdigest()

h1_hash_1 = _h1_json_hash()
h1_hash_2 = _h1_json_hash()
check("H1 JSON format byte-identical on repeated call",
      h1_hash_1 == h1_hash_2)

print(f"  INFO  H2 JSON SHA-256 (first 16): {digest_1[:16]}...")
print(f"  INFO  H1 JSON SHA-256 (first 16): {h1_hash_1[:16]}...")


# ---------------------------------------------------------------------------
print(f"\n{'='*50}")
print(f"RESULTS: {passes} passed, {fails} failed")
if fails > 0:
    sys.exit(1)
