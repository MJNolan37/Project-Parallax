# calibration/: status of every file

Everything in this directory is **experimental A1 calibration code and historical output**. Nothing here is a calibration protocol or a frozen critical value. Read `docs/A1_STATUS.md` first.

**Do not run or cite `calibrate_udmax.py` as the current calibration protocol.** It is kept only so the historical record stays reproducible.

## File status

| File | Status | Notes |
|---|---|---|
| `udmax_core.c` | Experimental | Limiting-law engine (C, built via ctypes). Includes the 1/m normalization fix. Comment-sanitized derivative; the object code is byte-identical to the original (see `docs/VALIDATION.md` §4). |
| `a1_grid_continuation.py` | Experimental | Separate-grid driver that produced `grid_T*.json`. Docstring-sanitized derivative. |
| `calibrate_udmax.py` | **SUPERSEDED** | First harness. Contains **rejected** acceptance rules (below). Sanitized derivative of the docstring and banner string. |
| `bench_M5.json` | Report-only | M = 5 benchmark: 0.95 quantile 8.8696396, 95% MC interval [8.8322432, 8.9089821]. No acceptance rule frozen. |
| `grid_T1000.json`, `grid_T2000.json`, `grid_T4000.json` | **NONCANONICAL** | Separate-grid M = 2 estimates. The grids share random-number streams; they are not independent samples. |
| `a1_grid_summary.json` | **NONCANONICAL** | Summary of the three grids, with hashes of the original sources. |
| `result.json` | **SUPERSEDED** | First-harness output. See the flags below. |
| `config.json`, `hashes.json` | **SUPERSEDED** | First-harness run record and the original source hashes. |
| `a1_nested_feasibility_probe.md` | Diagnostic | 200-path feasibility probe on a non-production seed. Not a calibration. |

## Rejected rules in `calibrate_udmax.py`

| Line | Code | Why it is rejected |
|---|---|---|
| 152 | `bm_pass = bm_err <= 0.20` | Benchmark pass/fail on a ±0.20 tolerance that was never part of the frozen design. Rejected; the benchmark is now reported as Monte Carlo interval containment only. |
| 25, 174–177 | `N_GC = 200_000`, grid check at T = 2,000 with seed + 1 | Grid-convergence check on a reduced path count and a different seed. Not the frozen protocol. |
| 134 | `Path("/home/claude/calibration")` | Hard-coded path from the original build workspace. The script will not run unmodified elsewhere. |

## How to read `result.json`

- **`benchmark_pass: true`** was computed under the rejected ±0.20 rule. **It is not a benchmark acceptance.**
- **`replication_pass: true`** covers only the two-decimal comparison of 500k vs 1M paths. The interval-width condition was never evaluated.
- **`grid_convergence_pass: false`** comes from the reduced 200k-path check. The full 1M-path grids also fail the 0.01 criterion.
- **`STATUS: CANDIDATE_NOT_YET_FROZEN`** is still accurate. Nothing is frozen.

## Hash references

`hashes.json` and `a1_grid_summary.json` record the hashes of the **original** sources, because those files produced the outputs. The shipped sources are comment-sanitized derivatives. The mapping:

| File | Original (produced the outputs) | Shipped |
|---|---|---|
| `udmax_core.c` | `78092ca4e6a3ff2790a3426b654b1b94d9eb4d55774628815de597e9be21fe43` | `94bfd188d95c0fff1f471e294ef944018b7b3b91916a6eb89aa11d4a7f735ddc` |
| `a1_grid_continuation.py` | `648528e079fe97101e4ed15a38b6793757e2f8ca2dd48ca26ba10ea6e3d35988` | `cdedc7fdda999cfdc50f07b104d558005fdf6406c5b1f659be3913adeee0738c` |
| `calibrate_udmax.py` | `f6eb271eccc4354c647c6e3c2e6fac8a58039c301529265a5a5bfe5082401a4d` | `e5c0ab81c26d73bb3c6ead77547dc09c5bd551d693049c8f589aef1e3bfd8c46` |

The originals are preserved unchanged in the project archive.

## Not in this repository (archive only)

| Artifact | SHA-256 |
|---|---|
| `udmax_core.so` (Linux x86_64 build of the original source) | `7912fe44d8762366835916d45d75dc34f8d9c195df9d5719f764699c84b2783b` |
| Raw per-batch simulation arrays (31 `.npy` files), packaged as `parallax-a1-raw-batches.zip` | `1cdb8b9b44bcda39b7060dd88e91ae9d1a9d57dadcb74e237e80504e42b5f244` |
| Per-batch records `grid/*.json` (30 files) | Listed in the archive recovery inventory |

To build the engine locally, use the recorded flags. They are machine-specific, so results may differ in the last bits:

```bash
gcc -O3 -march=native -ffast-math -fopenmp -shared -fPIC -o calibration/udmax_core.so calibration/udmax_core.c -lm
```

Building is not a calibration, and running the drivers produces no frozen value.
