# A1 Status: H1 First-Stage Critical Value (UNRESOLVED)

**Status: BLOCKED.**

- The 5% critical value for the frozen H1 first-stage statistic is **not frozen**.
- The H1 decision rule cannot be executed.
- No empirical H1/H2 analysis has been conducted.
- The code in `calibration/` is experimental. It is **not** a calibration protocol, and nothing in it is a canonical result.

## The problem

The preregistration (§3) specifies a pure-intercept Bai–Perron UDmax test with at most two breaks: M = 2, ε = 0.15, q = 1, at 5%. Published Bai–Perron tables at ε = 0.15 give the double-maximum value for M = 5, not M = 2. The widely cited 8.88 is that M = 5 value, so it cannot serve as the M = 2 threshold.

Addendum A1 was set up to calibrate the missing value by simulation. **Its authoritative text has not been designated for this repository and is not reproduced or reconstructed here.**

## What exists (experimental; see `calibration/SUPERSEDED.md` for per-file status)

**Simulator.** Monte Carlo simulation of the Bai–Perron asymptotic limit on a discretized Wiener path (`calibration/udmax_core.c`, `calibration/a1_grid_continuation.py`). The first implementation omitted the 1/m normalization of the m-break F statistic. The published M = 5 benchmark comparison exposed this before any M = 2 value was used. The current source includes the fix.

**Benchmark, report-only.**

| Item | Value |
|---|---|
| Statistic | M = 5, ε = 0.15, q = 1 |
| Grid and paths | 1,000-point grid, 200,000 paths |
| Simulated 0.95 quantile | 8.8696396 |
| 95% Monte Carlo interval | [8.8322432, 8.9089821] |
| Published value 8.88 | Inside the interval |

No acceptance rule was frozen for this comparison. It is a reported observation, not a known-answer validation.

**Separate-grid M = 2 estimates (NONCANONICAL).** The grids were run separately but share random-number streams, so they are not independent samples.

| Grid | 0.95 quantile | Change from previous grid |
|---|---|---|
| T = 1,000 | 8.8546 | – |
| T = 2,000 | 8.9368 | 0.0822 |
| T = 4,000 | 9.0040 | 0.0672 |

Each grid used 1,000,000 paths. The estimates rise as the grid is refined, and the 0.01 grid-convergence criterion specified for A1 was not met. These are finite-grid estimates. None is a critical value.

**Nested common-path design.** The build assistant's feasibility audit (2026-10-05) found it implementable with specific corrections. That is a feasibility finding, not acceptance of the design. It has not been run as a calibration.

## Current methods boundary

**Missing record.** A prior-session report, not verified here, states that an independent methods review returned on 2026-10-05 with the conclusion "further methods work required". The exact response has **not been recovered** and is **not ratified**. Nothing in this repository treats it as formally accepting any technique (including nested common paths or paired whole-path resampling) or as establishing any particular stopping or extrapolation requirement. Unrelated general research advice received since then is not a substitute for that record.

The project's methods-gap memo, as summarized by the project owner (the memo is not reproduced here), concludes there is **no defensible continuous-limit stopping rule yet**:

- The last paired-grid increment cannot certify the remaining discretization bias.
- Richardson extrapolation, geometric-tail assumptions and empirically stable increments are not substitutes for a validated error bound.

The research memos behind this status, cited by title only (titles as provided by the project owner; dates and contents not reproduced here):

- *Project Parallax — Research Orientation Memo*
- *UDmax Calibration Memo: Frozen M=2, ε=0.15 H1*
- *Efficient Continuous-Limit Calibration for Bai–Perron UDmax*
- *A1 Final Methods Gap: Continuous-Limit Stopping and Extrapolation*

## What this does not claim

- No M = 2 critical value, provisional or otherwise.
- No independent reproduction of any simulation result.
- No choice between the published-table numerical convention and the continuous-time limit as the calibration target. That adjudication is open.

## Unresolved governance records

- Authoritative Addendum A1 text: **not designated**.
- The exact 2026-10-05 methods review response: **not recovered**; ratification **deferred**.
- Pre-freeze READY / CLARIFICATIONS / BLOCKER implementation audit record: **missing**.
