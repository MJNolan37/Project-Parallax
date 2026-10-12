# A1 nested-grid feasibility probe (diagnostic only — not production)

Probe seed 12345 (not MASTER_SEED), N=200 paths, finest T=16000, coarse paths by
summing r adjacent N(0,1) increments and dividing by sqrt(r). Existing engine
`compute_udmax_m2` (corrected 1/m), tau_min = (15*T+99)//100.

Trimming exactness: 0.15*T evaluates exactly to 150, 300, 600, 1200, 2400.

Pathwise UDmax differences (finer - coarser), N=200:

| step | min diff | violations < -1e-9 | mean diff |
|---|---|---|---|
| 1000->2000 | -2.5e-14 | 0 | 0.0716 |
| 2000->4000 | -3.6e-14 | 0 | 0.0423 |
| 4000->8000 | -5.8e-14 | 0 | 0.0330 |
| 8000->16000 | -8.8e-14 | 0 | 0.0254 |

Negative minima are floating-point rounding (different arithmetic path), not violations.
Mean diffs are N=200 descriptive values only; not quantile estimates.

Runtime (2 OMP threads): 0.15 / 0.48 / 1.96 / 7.54 / 29.83 ms per path
-> ~40 ms per path all levels -> ~67 min for 100k paths; ~11 h for 1M.

RNG: PCG64 standard_normal draws are invariant to sub-batch chunking (verified).
