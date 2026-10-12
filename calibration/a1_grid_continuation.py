"""
Project Parallax A1 Grid Continuation (resumable, per-batch persistence).

Frozen protocol (unchanged from calibrate_udmax.py):
  MASTER_SEED=20261003, PCG64 via SeedSequence(seed).spawn(10), 10 x 100,000 paths,
  each batch generated in 10,000-path sub-batches (identical draw order to T=1000 run),
  eps=0.15, tau_min=ceil(eps*T), q=1, M=2, alpha=0.05,
  quantile = sorted[ceil(0.95 n)-1] (no interpolation),
  convergence gate |CV_fine - CV_prev| <= 0.01.
Benchmark: M=5, T=1000, seed MASTER_SEED+9999, 2 x 100,000 paths. No PASS/FAIL rule.

Usage:
  python a1_grid_continuation.py bench
  python a1_grid_continuation.py run   T b_lo b_hi     # batches [b_lo, b_hi)
  python a1_grid_continuation.py final T
  python a1_grid_continuation.py summary
"""
import ctypes, hashlib, json, os, resource, sys, time
from pathlib import Path
import numpy as np
from scipy.stats import binom

os.environ.setdefault("OMP_NUM_THREADS", "2")
MASTER_SEED, BM_SEED = 20261003, 20261003 + 9999
EPS, Q_LEVEL, CONV_TOL = 0.15, 0.95, 0.01
N_BATCH, BATCH_SIZE, SUB_BATCH = 10, 100_000, 10_000
BM_BATCHES = 2

HERE = Path(__file__).parent
GRID = HERE / "grid"; GRID.mkdir(exist_ok=True)

_lib = ctypes.CDLL(str(HERE / "udmax_core.so"))
_P = ctypes.POINTER(ctypes.c_double)
_lib.compute_udmax_m2.argtypes = [_P, ctypes.c_int, ctypes.c_int, ctypes.c_int, _P]
_lib.compute_udmax_Mmax.argtypes = [_P, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, _P]


def _stat(z, T, M):
    z = np.ascontiguousarray(z, dtype=np.float64)
    r = np.empty(z.shape[0])
    tau_min = int(np.ceil(EPS * T))
    if M == 2:
        _lib.compute_udmax_m2(z.ctypes.data_as(_P), z.shape[0], T, tau_min, r.ctypes.data_as(_P))
    else:
        _lib.compute_udmax_Mmax(z.ctypes.data_as(_P), z.shape[0], T, tau_min, M, r.ctypes.data_as(_P))
    return r


def rngs(n, seed):
    return [np.random.Generator(np.random.PCG64(c)) for c in np.random.SeedSequence(seed).spawn(n)]


def q95(a):
    return float(np.sort(a)[int(np.ceil(Q_LEVEL * len(a))) - 1])


def ci95(a):
    n, s = len(a), np.sort(a)
    lo, hi = int(binom.ppf(0.025, n, Q_LEVEL)), int(binom.ppf(0.975, n, Q_LEVEL))
    return float(s[lo - 1]), float(s[hi - 1])


def peak_rss_mb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def batch(rng, T, M):
    return np.concatenate([_stat(rng.standard_normal((SUB_BATCH, T)), T, M)
                           for _ in range(BATCH_SIZE // SUB_BATCH)])


def cmd_bench():
    t0 = time.time()
    a = np.concatenate([batch(r, 1000, 5) for r in rngs(BM_BATCHES, BM_SEED)])
    np.save(GRID / "bench_M5_T1000.npy", a)
    lo, hi = ci95(a)
    res = dict(M=5, T=1000, eps=EPS, q=1, n_paths=len(a), seed=BM_SEED, cv=q95(a),
               ci_lo=lo, ci_hi=hi, target=8.88, target_inside=bool(lo <= 8.88 <= hi),
               elapsed_s=time.time() - t0, peak_rss_mb=peak_rss_mb())
    (HERE / "bench_M5.json").write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))


def cmd_run(T, b_lo, b_hi):
    rs = rngs(N_BATCH, MASTER_SEED)
    for b in range(b_lo, b_hi):
        f = GRID / f"T{T}_b{b}.npy"
        if f.exists():
            print(f"T={T} b{b}: exists, skip"); continue
        t0 = time.time()
        a = batch(rs[b], T, 2)
        np.save(f, a)
        meta = dict(T=T, batch=b, q95=q95(a), elapsed_s=time.time() - t0, peak_rss_mb=peak_rss_mb())
        (GRID / f"T{T}_b{b}.json").write_text(json.dumps(meta))
        print(json.dumps(meta), flush=True)


def cmd_final(T):
    parts = [np.load(GRID / f"T{T}_b{b}.npy") for b in range(N_BATCH)]
    metas = [json.loads((GRID / f"T{T}_b{b}.json").read_text()) for b in range(N_BATCH)]
    a = np.concatenate(parts)
    lo, hi = ci95(a)
    cv500 = q95(np.concatenate(parts[:5]))
    res = dict(T=T, tau_min=int(np.ceil(EPS * T)), n_paths=len(a), cv=q95(a), cv_2dec=round(q95(a), 2),
               ci_lo=lo, ci_hi=hi, cv_500k=cv500, rep_2dec_equal=round(cv500, 2) == round(q95(a), 2),
               batch_q95=[m["q95"] for m in metas],
               runtime_s=sum(m["elapsed_s"] for m in metas),
               peak_rss_mb=max(m["peak_rss_mb"] for m in metas),
               z_subbatch_mb=SUB_BATCH * T * 8 / 1e6)
    (HERE / f"grid_T{T}.json").write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))


def cmd_summary():
    Ts = sorted(int(p.stem.split("_T")[1]) for p in HERE.glob("grid_T*.json"))
    rows = [json.loads((HERE / f"grid_T{T}.json").read_text()) for T in Ts]
    for prev, cur in zip(rows, rows[1:]):
        cur["diff_vs_prev"] = abs(cur["cv"] - prev["cv"])
        cur["gate_pass"] = cur["diff_vs_prev"] <= CONV_TOL
    files = ["udmax_core.c", "udmax_core.so", "a1_grid_continuation.py", "bench_M5.json"] + \
            [f"grid_T{T}.json" for T in Ts]
    out = dict(levels=rows, hashes={f: sha(HERE / f) for f in files})
    (HERE / "a1_grid_summary.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    c = sys.argv[1]
    if c == "bench": cmd_bench()
    elif c == "run": cmd_run(int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]))
    elif c == "final": cmd_final(int(sys.argv[2]))
    elif c == "summary": cmd_summary()
