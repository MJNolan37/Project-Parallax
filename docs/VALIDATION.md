# Phase 2.1 Validation Record (Disclosure Snapshot)

**What this covers.** The Phase 2.1 implementation in `src/phase2/` has been validated against synthetic and known-answer tests only.

- **No empirical H1/H2 analysis has been conducted.**
- **This is not independent validation.** Independent reproduction is still an open gate.
- **This record supports a code-and-specification disclosure.** It is not the Phase 2.1 release described in §11 of the preregistration, and it does not open the empirical execution gate.

Governing specification: `docs/phase2_preregistration_v1.0.md`, a format conversion of the governing DOCX.

---

## 1. Test evidence

**Current status:** in the most recent run (1e, Windows review of the restored package), 263 checks passed and 0 failed across six suites. Eight R-dependent Bai–Perron checks were skipped, and the separate H1 HAC R-reference gate ran but skipped. This does not complete the empirical execution gate.

The evidence sets below are kept separate because they ran at different times, on different copies, in different environments, and by different parties.

### 1a. Earlier evidence (2026-10-03, original files, build workspace)

| Suite | Result |
|---|---|
| `tests/test_phase2_hac.py` | 34 passed |
| `tests/test_phase2_h2.py` | 70 passed |
| `tests/test_phase2_integration.py` | 82 passed |

That is 186 checks, all passing, as recorded in the build session's records. **The environment versions were not recorded at the time.** The other suites have no recorded result from this date.

### 1b. Recovery re-run (2026-10-11, recovered original files, cloud workspace)

Environment: Python 3.11.15, numpy 2.4.4, scipy 1.17.1, pandas 3.0.2, Linux x86_64. rpy2, R and pytest were not installed.

| Suite | Result |
|---|---|
| hac | 34 passed, 0 failed |
| h2 | 70 passed, 0 failed |
| integration | 82 passed, 0 failed |
| bootstrap | 33 passed, 0 failed |
| bai_perron | 23 passed, 0 failed, **8 skipped** (rpy2 not available) |

### 1c. Owner's local re-run (2026-10-11, recovered original files, Windows)

Reported result: all five suites above with the same counts, which is 242 executed checks passing and 8 skipped. **The local Python and package versions have not yet been recorded here.**

### 1d. Disclosure-snapshot run (2026-10-11T13:44Z, this branch)

This run used the files exactly as proposed for this snapshot, including the comment-sanitized sources in section 4. It ran on the preparation branch at `bc05c48` with the new files uncommitted. Environment as in 1b.

| Suite | Result |
|---|---|
| hac | 34 passed, 0 failed |
| h2 | 70 passed, 0 failed |
| integration | 82 passed, 0 failed |
| bootstrap | 33 passed, 0 failed |
| bai_perron | 23 passed, 0 failed, **8 skipped** (rpy2 not available) |
| **Total** | **242 passed, 0 failed, 8 skipped** |

### 1e. Windows review of the restored package (2026-10-11, reported by the orchestrating reviewer)

This run used the restored disclosure package on Windows. **Source:** the reviewer's local review evidence archive (`track1-local-review-evidence-2026-10-11.zip`), as reported. The preparer of this document has not inspected that archive.

Environment: Python 3.12.14, NumPy 2.5.4, SciPy 1.17.1, pandas 3.0.1, pytest 9.1.1.

| Suite | Result |
|---|---|
| hac, h2, integration, bootstrap, bai_perron | 242 passed, 0 failed, **8 Bai–Perron R checks skipped** |
| transform (`python -m pytest tests/test_phase2_transform.py`) | 21 passed |
| **Combined executed total** | **263 passed, 0 failed** |
| H1 HAC R-reference gate (`tests/test_phase2_hac_rpy2.py`) | Executed; **SKIP** (exit 0). Not a validation pass. |

### 1f. Not executed or not passed

| Item | Reason |
|---|---|
| `tests/test_phase2_transform.py` | Not run in 1a–1d (pytest unavailable there). **Executed only in 1e: 21 passed.** |
| `tests/test_phase2_hac_rpy2.py` (H1 HAC R-reference gate) | **Never passed.** Executed in 1d and 1e; both times it printed "H1 HAC GATE: SKIP — pre-execution obligation not yet satisfied" and **exited 0**. That exit code is not a pass. Reason: R/rpy2 unavailable and the reference constants `REF_SERIES` / `REF_LRV` are unfilled. |
| 8 R-dependent checks in `tests/test_phase2_bai_perron.py` | Skipped in every run (rpy2 absent): single-break recovery, CI and segment means; two-break detection, tolerance and segment count; zero-break non-significance; minimum-segment enforcement in break CIs. |
| `diagnostics/phase2_provenance_check.py` | Not run. It reads empirical input files, which the stop gate excludes. |

### Commands

From the repository root:

```bash
python tests/test_phase2_hac.py
python tests/test_phase2_h2.py
python tests/test_phase2_integration.py
python tests/test_phase2_bootstrap.py
python tests/test_phase2_bai_perron.py      # R checks SKIP without rpy2
python -m pytest tests/test_phase2_transform.py   # requires pytest
python tests/test_phase2_hac_rpy2.py        # requires R + rpy2 and filled reference constants
```

---

## 2. Input-checksum enforcement (disclosed gap)

Read from `config/phase2_spec.toml` and `diagnostics/phase2_provenance_check.py`. The script was not executed.

| Input | Checksum field | Enforcement |
|---|---|---|
| Aggregate input `data/clmx_monthly_decomp_opt_b.csv` | `clmx_monthly_decomp_opt_b_sha256 = ""` (blank) | Blank, so the provenance check halts before any empirical run (fail-closed). No expected value has been committed. |
| FF49 crosswalk | `ff49_crosswalk_sha256 = ""` (blank) | **Not enforced.** Even if filled, the script only prints a note: the file path is not wired in, and no comparison is made. |
| FF12 sector inputs | **No checksum field exists** | **Not enforced.** |

These must be resolved before the empirical execution gate can open (preregistration §10 and §11).

---

## 3. Other open validation items

- **No dependency lock.** No lockfile exists; `config/phase2_spec.toml` refers to `requirements-phase2-lock.txt`, which is not present.
- **H2 eligibility wording (watchpoint, unresolved).**
  - Preregistration §2 fixes Phase 1 "Option B complete_month" missing-data treatment.
  - §6 specifies sector CLMX "using Phase 1 Option B and at least ten valid daily return days".
  - `src/phase2/h2_system.py` (line 386) documents ">= 10 valid daily return days".

  The code matches the ten-day phrase, but that does not resolve how §6 relates to `complete_month`. This needs adjudication. It has not been changed here.
- **Pre-freeze implementation audit missing.** The pre-freeze READY / CLARIFICATIONS / BLOCKER implementation audit record has not been located.
- **The A1 critical value is unresolved.** See `docs/A1_STATUS.md`. The H1 decision rule cannot be executed until it is resolved.

---

## 4. Source provenance for this snapshot

Every proposed code, test and config file matches the recovered file byte for byte, except the five comment-sanitized derivatives listed in the second table. Those had private assistant labels replaced in comments, docstrings or one banner string. The recovered originals are preserved unchanged in the project archive.

| File | Recovered SHA-256 = shipped SHA-256 |
|---|---|
| `src/phase2/__init__.py` | `6030959b71cb8d980ffb5c06bd1f6cc1ec6d11a40bfe0ec845274263d523aa7b` |
| `src/phase2/bai_perron.py` | `c43b37cca28f2b5333040164a4027b0489a651deadc4070e19ae7bea9ef652a4` |
| `src/phase2/bootstrap.py` | `ef1890d7cfd4b32d06c09ccf11cfc679a4b7b86d0ad606a104fe72c8adfa0d8b` |
| `src/phase2/reporting.py` | `1bc5fca9ce2070ddfdc379a1c3d1489a3f66e52c07a4574179d3e6039820bbf0` |
| `src/phase2/robustness.py` | `d53862cb7df6735d05e65cf5f84b864cae82560ce205f3a9a3801cfcd777efd3` |
| `src/phase2/transform.py` | `8c0b25d0e9cecefdf5cef5121e81233983abfce7b08f06ec53d667de52a0ece8` |
| `tests/test_phase2_hac.py` | `b135f30be87508c5aafef71fc660d413a08eb4b606630f083d805078e3a31f2d` |
| `tests/test_phase2_h2.py` | `ddfab250b3b0660a7d946f120c71a0c0dfcc648215daef083ce7f60a1e1f0568` |
| `tests/test_phase2_integration.py` | `87f4cab0ab0477db1b0766cf424cb956eed97d80daf0649c0a9f23767e0d39d5` |
| `tests/test_phase2_bootstrap.py` | `3058615e2fa02d6614c10131ebcb06ed011ce7a2f718f3fc774812ca2ea61df6` |
| `tests/test_phase2_bai_perron.py` | `9f6f90086df43c62217b38f01e0b4828afc992dca7e2c3c77ab1e3aa482b1b5e` |
| `tests/test_phase2_transform.py` | `cb7f34a6a2e5c2efb7334fe50cb6ff8484fcd140bc21cf959d63e6769d84f5b9` |
| `tests/test_phase2_hac_rpy2.py` | `58252e611a059ce31b2801aa15d6574e118b99aad2fc61ed76bee437f1407c92` |
| `config/phase2_spec.toml` | `f7c68812440b2271265d57bbc5a9239b10aa6c500cd1a88206bcfa3411f57c3a` |
| `diagnostics/phase2_provenance_check.py` | `00957ae00b8a6899bbd462d13b6ea9745afa882c3b3d0b81eecfb7b5612645d8` |

| Sanitized derivative | Recovered (original) SHA-256 | Shipped (sanitized) SHA-256 | Change | Equivalence check |
|---|---|---|---|---|
| `src/phase2/h2_system.py` | `f31734d4b4cbecef7b13aa38d3f558ae88661b091fa6b1b52c736107511dbbbd` | `bf6d3ff20ce64fad86bddd77b98516d7b48540019ccb3a92a720fffaa4d77b16` | Comment, line 478 | Python AST identical |
| `src/phase2/hac.py` | `43d1347982e9eb498e2672dedf6ed51a51e722fa78421c532d85db0bffde0472` | `739fa6a93611feefdcc95d7a9bbd6916139d222d912d04e7e2dcd3269df937e8` | Docstring, line 299 | AST differs only in that docstring |
| `calibration/udmax_core.c` | `78092ca4e6a3ff2790a3426b654b1b94d9eb4d55774628815de597e9be21fe43` | `94bfd188d95c0fff1f471e294ef944018b7b3b91916a6eb89aa11d4a7f735ddc` | Comment, line 2 | Object code byte-identical (`gcc -O3 -fopenmp -c`) |
| `calibration/a1_grid_continuation.py` | `648528e079fe97101e4ed15a38b6793757e2f8ca2dd48ca26ba10ea6e3d35988` | `cdedc7fdda999cfdc50f07b104d558005fdf6406c5b1f659be3913adeee0738c` | Module docstring, line 2 | AST differs only in the module docstring |
| `calibration/calibrate_udmax.py` (SUPERSEDED) | `f6eb271eccc4354c647c6e3c2e6fac8a58039c301529265a5a5bfe5082401a4d` | `e5c0ab81c26d73bb3c6ead77547dc09c5bd551d693049c8f589aef1e3bfd8c46` | Module docstring, line 2; printed banner string, line 138 | AST differs only in those two string constants |

The historical calibration records (`calibration/hashes.json`, `calibration/a1_grid_summary.json`) reference the **original** hashes, because those were the files that produced them.
