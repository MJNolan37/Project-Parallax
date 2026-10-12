"""
Project Parallax A1 Blind UDmax Calibration Harness
Bai-Perron asymptotic Wiener-process limiting law
UDmax(M=2) = max{supF(0|1), supF(0|2)}, q=1, eps=0.15

CANDIDATE — NOT YET FROZEN
"""

import numpy as np
import json, hashlib, time, sys, ctypes, os
from pathlib import Path

# ─── Frozen numerical protocol ────────────────────────────────────────────────
MASTER_SEED = 20261003
T_BASE      = 1000
T_FINE      = 2000
EPS         = 0.15
N_PROD      = 1_000_000
N_BATCH     = 10
BATCH_SIZE  = N_PROD // N_BATCH      # 100_000
SUB_BATCH   = 10_000
Q_LEVEL     = 0.95

# Diagnostic-only paths (not frozen at 1M)
N_GC       = 200_000
N_BM       = 200_000
GC_BATCHES = 2
BM_BATCHES = 2


# ─── C extension ─────────────────────────────────────────────────────────────
_HERE = Path(__file__).parent
_lib  = None

def _load_lib():
    global _lib
    if _lib is not None:
        return _lib
    so = _HERE / "udmax_core.so"
    if not so.exists():
        raise FileNotFoundError(f"udmax_core.so not found at {so}")
    os.environ.setdefault("OMP_NUM_THREADS", "2")
    lib = ctypes.CDLL(str(so))
    _dptr = ctypes.POINTER(ctypes.c_double)
    lib.compute_udmax_m2.argtypes = [_dptr, ctypes.c_int, ctypes.c_int, ctypes.c_int, _dptr]
    lib.compute_udmax_m2.restype  = None
    lib.compute_udmax_Mmax.argtypes = [_dptr, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, _dptr]
    lib.compute_udmax_Mmax.restype  = None
    _lib = lib
    return lib

def _dptr(arr):
    return arr.ctypes.data_as(ctypes.POINTER(ctypes.c_double))


# ─── Public computation interface ─────────────────────────────────────────────
def udmax_m2_sub(z_sub: np.ndarray, T: int, tau_min: int) -> np.ndarray:
    """Compute UDmax(M=2) for each path via C extension."""
    lib = _load_lib()
    z_c = np.ascontiguousarray(z_sub, dtype=np.float64)
    n   = z_c.shape[0]
    result = np.empty(n, dtype=np.float64)
    lib.compute_udmax_m2(_dptr(z_c), n, T, tau_min, _dptr(result))
    return result


def udmax_Mmax_sub(z_sub: np.ndarray, T: int, tau_min: int, M_max: int) -> np.ndarray:
    """Compute UDmax(M=M_max) for each path via C extension DP."""
    lib = _load_lib()
    z_c = np.ascontiguousarray(z_sub, dtype=np.float64)
    n   = z_c.shape[0]
    result = np.empty(n, dtype=np.float64)
    lib.compute_udmax_Mmax(_dptr(z_c), n, T, tau_min, M_max, _dptr(result))
    return result


# ─── RNG ─────────────────────────────────────────────────────────────────────
def make_rngs(n_batch: int, seed: int):
    """Deterministic non-overlapping PCG64 streams via SeedSequence."""
    ss = np.random.SeedSequence(seed)
    return [np.random.Generator(np.random.PCG64(c)) for c in ss.spawn(n_batch)]


# ─── Batch runner ─────────────────────────────────────────────────────────────
def run_batches(T: int, batch_rngs: list, batch_size: int,
                M_max: int = 2, label: str = "") -> tuple:
    """Returns (stats_per_batch, batch_q95s, elapsed)."""
    tau_min  = int(np.ceil(EPS * T))
    n_subs   = batch_size // SUB_BATCH
    all_stats, batch_q95s = [], []
    t0 = time.time()
    for b, rng in enumerate(batch_rngs):
        parts = []
        for _ in range(n_subs):
            z = rng.standard_normal((SUB_BATCH, T))
            s = (udmax_m2_sub(z, T, tau_min) if M_max == 2
                 else udmax_Mmax_sub(z, T, tau_min, M_max))
            parts.append(s)
        ba = np.concatenate(parts)
        all_stats.append(ba)
        idx = int(np.ceil(Q_LEVEL * batch_size)) - 1
        bq  = float(np.sort(ba)[idx])
        batch_q95s.append(bq)
        print(f"  [{label}] b{b+1}/{len(batch_rngs)}: q95={bq:.4f}  "
              f"({time.time()-t0:.1f}s)", flush=True)
    return all_stats, batch_q95s, time.time() - t0


def quantile_os(arr: np.ndarray) -> float:
    """Order-statistic 0.95 quantile, no interpolation."""
    idx = int(np.ceil(Q_LEVEL * len(arr))) - 1
    return float(np.sort(arr)[idx])


def ci_95(arr: np.ndarray):
    """95% MC CI for population 0.95 quantile via binomial order stats."""
    from scipy.stats import binom
    n  = len(arr)
    lo = int(binom.ppf(0.025, n, Q_LEVEL))
    hi = int(binom.ppf(0.975, n, Q_LEVEL))
    s  = np.sort(arr)
    return float(s[lo - 1]), float(s[hi - 1])


def sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    out = Path("/home/claude/calibration")
    out.mkdir(exist_ok=True)

    print("=" * 64)
    print("Project Parallax A1 UDmax Calibration Harness")
    print(f"Master seed  : {MASTER_SEED}")
    print(f"RNG          : numpy {np.__version__} PCG64 / SeedSequence")
    print(f"Python       : {sys.version.split()[0]}")
    print(f"OMP_NUM_THREADS : {os.environ.get('OMP_NUM_THREADS','2')}")
    print("=" * 64, flush=True)

    # ── [1] BENCHMARK GATE M=5 ────────────────────────────────────────
    print(f"\n[1] Benchmark gate M=5, T={T_BASE}, eps={EPS}: target 8.88")
    bm_rngs  = make_rngs(BM_BATCHES, MASTER_SEED + 9999)
    bm_stats, bm_bq, bm_t = run_batches(
        T_BASE, bm_rngs, N_BM // BM_BATCHES, M_max=5, label="BM5")
    bm_cv   = quantile_os(np.concatenate(bm_stats))
    bm_err  = abs(bm_cv - 8.88)
    bm_pass = bm_err <= 0.20
    print(f"  M=5 cv={bm_cv:.4f}  |err|={bm_err:.4f}  "
          f"{'PASS' if bm_pass else 'FAIL — ABORTING'}", flush=True)
    if not bm_pass:
        sys.exit(1)

    # ── [2] M=2 PRODUCTION ────────────────────────────────────────────
    print(f"\n[2] M=2 production: {N_PROD:,} paths, T={T_BASE}")
    prod_rngs  = make_rngs(N_BATCH, MASTER_SEED)
    prod_stats, prod_bq, prod_t = run_batches(
        T_BASE, prod_rngs, BATCH_SIZE, M_max=2, label="M2")
    all_arr  = np.concatenate(prod_stats)
    cv_1m    = quantile_os(all_arr)
    ci_lo, ci_hi = ci_95(all_arr)

    # ── [3] REPLICATION-CONVERGENCE (500K = first 5 batches) ─────────
    cv_500k  = quantile_os(np.concatenate(prod_stats[:5]))
    rep_pass = round(cv_500k, 2) == round(cv_1m, 2)
    print(f"\n[3] Replication: cv_500k={cv_500k:.4f}  cv_1m={cv_1m:.4f}  "
          f"{'PASS' if rep_pass else 'FAIL'}", flush=True)

    # ── [4] GRID-CONVERGENCE T=2000 ───────────────────────────────────
    print(f"\n[4] Grid convergence: T={T_FINE}, {N_GC:,} paths")
    gc_rngs  = make_rngs(GC_BATCHES, MASTER_SEED + 1)
    gc_stats, gc_bq, gc_t = run_batches(
        T_FINE, gc_rngs, N_GC // GC_BATCHES, M_max=2, label="GC")
    cv_2000  = quantile_os(np.concatenate(gc_stats))
    gc_diff  = abs(cv_2000 - cv_1m)
    gc_pass  = gc_diff <= 0.01
    print(f"  T=1000={cv_1m:.4f}  T=2000={cv_2000:.4f}  "
          f"|diff|={gc_diff:.4f}  {'PASS' if gc_pass else 'FAIL'}", flush=True)

    # ── Artifacts ─────────────────────────────────────────────────────
    config = {
        "master_seed":     MASTER_SEED,
        "T_base":          T_BASE,
        "T_fine":          T_FINE,
        "eps":             EPS,
        "tau_min_base":    int(np.ceil(EPS * T_BASE)),
        "tau_min_fine":    int(np.ceil(EPS * T_FINE)),
        "n_production":    N_PROD,
        "n_batches":       N_BATCH,
        "batch_size":      BATCH_SIZE,
        "sub_batch":       SUB_BATCH,
        "q_level":         Q_LEVEL,
        "quantile_method": "order_statistic_ceil_no_interpolation",
        "rng_algorithm":   "numpy_PCG64",
        "rng_seeding":     "SeedSequence.spawn",
        "numpy_version":   np.__version__,
        "python_version":  sys.version.split()[0],
        "c_extension":     "udmax_core.so (gcc -O3 -march=native -ffast-math -fopenmp)",
        "omp_threads":     os.environ.get("OMP_NUM_THREADS", "2"),
        "n_gc_paths":      N_GC,
        "n_bm_paths":      N_BM,
    }
    result = {
        "STATUS":                "CANDIDATE_NOT_YET_FROZEN",
        "M":                     2,
        "eps":                   EPS,
        "q":                     1,
        "T_base":                T_BASE,
        "cv_full_precision":     cv_1m,
        "cv_display":            round(cv_1m, 2),
        "ci_95_lo":              ci_lo,
        "ci_95_hi":              ci_hi,
        "batch_q95s":            prod_bq,
        "cv_500k":               cv_500k,
        "replication_pass":      rep_pass,
        "cv_2000":               cv_2000,
        "grid_convergence_diff": gc_diff,
        "grid_convergence_pass": gc_pass,
        "benchmark_M5_cv":       bm_cv,
        "benchmark_target":      8.88,
        "benchmark_error":       bm_err,
        "benchmark_pass":        bm_pass,
        "elapsed_prod_s":        prod_t,
    }

    (out / "config.json").write_text(json.dumps(config, indent=2))
    (out / "result.json").write_text(json.dumps(result, indent=2))

    src_sha = sha256(__file__)
    cfg_sha = sha256(out / "config.json")
    res_sha = sha256(out / "result.json")
    (out / "hashes.json").write_text(json.dumps(
        {"source_py":   src_sha,
         "source_c":    sha256(_HERE / "udmax_core.c"),
         "source_so":   sha256(_HERE / "udmax_core.so"),
         "config":      cfg_sha,
         "result":      res_sha}, indent=2))

    all_gates = bm_pass and gc_pass and rep_pass

    print("\n" + "=" * 64)
    print("A1 CALIBRATION RESULT  (CANDIDATE — NOT YET FROZEN)")
    print(f"  M=2  cv full precision : {cv_1m:.8f}")
    print(f"  M=2  cv two decimal    : {round(cv_1m, 2):.2f}")
    print(f"  95% MC CI              : [{ci_lo:.4f}, {ci_hi:.4f}]")
    print(f"  Batch q95s             : {[round(x, 4) for x in prod_bq]}")
    print(f"  cv_500k                : {cv_500k:.4f}")
    print(f"  cv_2000                : {cv_2000:.4f}")
    print(f"  Benchmark M=5          : {bm_cv:.4f}  {'PASS' if bm_pass else 'FAIL'}")
    print(f"  Grid convergence       : |diff|={gc_diff:.4f}  {'PASS' if gc_pass else 'FAIL'}")
    print(f"  Replication            : {'PASS' if rep_pass else 'FAIL'}")
    print(f"  source-py SHA-256      : {src_sha}")
    print(f"  config SHA-256         : {cfg_sha}")
    print(f"  result SHA-256         : {res_sha}")
    print("=" * 64)
    print(f"\n{'READY FOR INDEPENDENT REPRODUCTION' if all_gates else 'NEEDS CALIBRATION CORRECTION'}")
    return all_gates


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
