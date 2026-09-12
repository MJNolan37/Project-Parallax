# Changelog

All material changes to the Project Parallax research design, methodology, data strategy, and repository structure are documented here.

A change is "material" if it affects hypotheses, operationalizations, universe, dataset, factor model, attribution methodology, return frequency, research horizon, or project scope. Exploratory extensions and code improvements are noted but do not require the same level of documentation.

---

## [0.2.0] — 2026-09-12

### Phase 1 Hardening — Implementation Corrections, Governance, and Public Release

This release closes Phase 1 by repairing a latent implementation defect, adding a regression test, auditing the fill-method policy, updating dependencies, disambiguating empirical statistics, correcting survivorship language, and updating all public-facing documentation to reflect Phase 1 completion state.

### Fixed

- **Option A latent FIRM understatement defect** (`diagnostics/wp05_live_diagnostic.py`): The CLMX eps computation used `R[ticker] - r_j`, where `R[ticker]` is NaN for a stock missing on a given day. Because `(NaN**2).sum()` silently skips NaN terms, FIRM was understated by `Σ W_j × w_ij × (r_j,d)²` for each positive-weight ticker missing on day d. Fix: added `R_filled = R.fillna(0.0)` after weight normalization and used it consistently for mu_d, r_j, and eps. Under Option B (canonical for Phase 1), R has no NaN values, so this defect had zero impact on any Phase 1 empirical result. Under Option A, all 45 A-exclusive ticker-months had zero prior-month-end weight, making the defect numerically inert even for that path. Fix applied for correctness and forward safety.

- **Same Option A eps defect repaired** (`notebooks/02_historical_replication.ipynb`, cells `cell-step8-d018-fn` and `cell-step12-functions`): Both inline `decompose_month()` and `clmx_decompose_month()` functions updated with the `R_filled = R.fillna(0.0)` fix. Docstrings updated to document the fix rationale and reference `tests/test_clmx.py`.

- **pct_change fill policy** (`notebooks/02_historical_replication.ipynb`, cell `cell-step3-prices`): Changed `prices.pct_change()` to `prices.pct_change(fill_method=None)` to prevent implicit forward-filling of prices. Already applied in `wp05_live_diagnostic.py` (line 597) and `wp05_daily_weight_audit.py` (line 222) in prior sessions.

### Added

- **`tests/test_clmx.py`** — Standalone regression test suite for the Option A FIRM understatement defect. Eight test cases using a synthetic 2-stock / 2-day scenario with analytically derived expected values:
  - Defective FIRM = 0.00013440
  - Correct FIRM = 0.00019200
  - Gap = −5.76×10⁻⁵ = W_j × w_B × (r_j,d2)²
  - Option B invariance: both implementations agree when R has no NaN
  - MKT identity: mu_d identical under both paths for this case
  - No imports from the diagnostic module (avoids yfinance/matplotlib import chain)

  These tests document the defect and guard against reintroduction. They do not constitute evidence about H1.

### Changed

- **`requirements.txt`** — Added `lxml>=4.9.0` (required for Wikipedia HTML parsing of S&P 500 constituent table) and `pyarrow>=12.0.0` (required for `.parquet` cache read/write). Both discovered during Phase 1 live execution.

- **`RESEARCH_LOG.md`** — Full Phase 1 live execution history appended: D-018 and D-020 resolution, q_t audit results, Option A defect discovery and repair, pct_change audit, endpoint note (2024-12-30 vs 2024-12-31), FF49 parser repair, Wikipedia User-Agent fix, dependency discoveries, and G-Zephy Phase 1 Hardening scope.

- **`README.md`** — Status updated from "In progress" to Phase 1 complete. D-018 (Option B) and D-020 (2010–2024) shown as resolved. Empirical statistics added with explicit disambiguation (ratio of sums vs. mean of monthly ratios). Survivorship limitation stated explicitly with no directional claim on bias direction or magnitude. Roadmap Phase 1 row updated to complete.

- **FIRM share statistics disambiguated** throughout repository: the two statistics are distinct and must not be conflated:
  - **39.9490%** — FIRM / (MKT + IND + FIRM) as a ratio of the summed monthly components across all 180 months (ratio of total-period sums). Appropriate for total-period aggregate composition.
  - **46.3215%** — Arithmetic mean of the monthly FIRM / (MKT + IND + FIRM) ratio, computed month-by-month then averaged (mean of monthly ratios). Higher than the ratio-of-sums because months with low total variance carry disproportionately high FIRM share.

- **Survivorship language** — Removed all directional claims about survivorship bias effect on FIRM share. The direction and magnitude of the bias have not been empirically established for this dataset. The current-constituent limitation is stated as a documented constraint, not as evidence of any particular directional effect.

### Research State

- **D-018 RESOLVED:** Option B (`complete_month`) is canonical for Phase 1.
- **D-020 RESOLVED:** 2010–2024 (180 months). Extended window 2005–2009 failed the ≥85% coverage gate.
- **Phase 1 complete.** WP-05 historical replication executed, D-018 and D-020 resolved, implementation hardened, public repository updated. No hypothesis testing has occurred. Phase 2 has not been authorized.

---

## [0.1.0] — 2026-08-18

### Added

- Initial repository structure
- `README.md` — project overview, research question, hypotheses, analytical framework, roadmap
- `PROJECT_CHARTER.md` — full public research methodology and preregistration document
- `RESEARCH_LOG.md` — initial entry registering hypotheses, competing explanations, and open design decisions before analysis begins
- `docs/bibliography.md` — literature under active review (Phase 0)
- `docs/data_dictionary.md` — skeleton, to be completed during Phase 1
- `requirements.txt` — initial dependency list
- `src/validation.py` — survivorship bias and data quality diagnostic framework (stub)
- `src/attribution/brinson.py` — Brinson attribution engine (stub)
- `src/attribution/factors.py` — FF6 factor attribution module (stub)
- `tests/test_brinson.py` — known-answer Brinson validation tests (stub)
- `notebooks/01_data_validation.ipynb` — Phase 1 data feasibility notebook (skeleton)

### Research Design Baseline

- **H1 operationalization registered:** residual/specific variance share after systematic controls
- **Factor baseline registered:** Fama-French Five Factors + Momentum (FF6)
- **Prototype universe registered:** S&P 500 (provisional)
- **Brinson validation approach registered:** controlled synthetic portfolios with known expected attribution
- **Open decisions registered:** return frequency, historical horizon, final universe (all pending Phase 1)

---

## [0.1.1] — 2026-08-19

### Changed

- `PROJECT_CHARTER.md` Section 9: renamed "Portfolio C — Combined Active" to "Portfolio C — Combined Effects" to remove unintended active-portfolio connotation
- `PROJECT_CHARTER.md` Section 4 (H1): added literature context note acknowledging that the Campbell-Lettau-Malkiel-Xu secular trend did not persist cleanly post-2001; clarified that H1 is a directional hypothesis under investigation, not an assumed finding
- `src/attribution/factors.py`: added explicit model-dependence caveat clarifying that residual/specific return means "unexplained by this specification," not "inherently firm-specific"
- `src/validation.py`: softened "recommended handling" to "suggested data handling guidance"
- `docs/methodology.md`: added "Residual Return — Model Dependence" section; added "Primary comparative question" to Brinson section foregrounding the Brinson/factor comparative research output

### Rationale

Language audit and literature-informed refinement following Phase 0 preliminary findings. No hypothesis changes. No operationalization changes.

---

## [0.1.2] — 2026-08-19

### Added

- `notebooks/02_historical_replication.ipynb` — CLMX variance decomposition replication notebook (Phase 0/1 bridge). Implements the three-component MKT/IND/FIRM variance decomposition from Campbell, Lettau, Malkiel & Xu (2001) using the methodology confirmed by the authors' 2022 NBER restatement. Sections: mathematical framework, synthetic worked example, FF49 industry classification pipeline (EDGAR SIC codes + French crosswalk), full-period decomposition, visualization, directional comparison to CLMX (2022), and documented deviations.

### Changed

- `docs/bibliography.md` — Formalized from skeleton to annotated bibliography. Added entries for CLMX (2001), CLMX NBER WP 29916 (2022), Brandt/Brav/Graham/Kumar (2010), and Chiah/Gharghori/Zhong (2020) with status annotations. CLMX (2022) registered as primary post-2001 directional benchmark; Chiah et al. (2020) registered as secondary robustness comparator.

### Methodology Registrations

- **CLMX variance estimator confirmed:** Monthly variance = sum of raw squared daily return components (not demeaned, not normalized by trading-day count). Source: CLMX authors' own 2022 NBER restatement, Figure notes 1–4.
- **Post-2001 benchmark registered:** Campbell, Lettau, Malkiel & Xu (2022), NBER WP 29916, "Idiosyncratic Equity Risk Two Decades Later." Figures 2–4 are the directional comparison targets.
- **Secondary benchmark registered:** Chiah, Gharghori & Zhong (2020), *Critical Finance Review* — independent replication through 2016–2017.
- **Industry classification confirmed:** Fama-French 49 industries (not 48), as stated in CLMX (2001). Software/hardware split matters for modern S&P 500 composition.
- **Missing data convention:** Drop, not impute — consistent with EDGAR replication code.
- **Minimum observation threshold:** 10 trading days per month — documented as Project Parallax design choice, not a CLMX requirement.

### Open Decisions Unchanged

Return frequency (daily data/monthly aggregation) confirmed for replication stage. Primary VW weighting confirmed. Survivorship bias assessment and universe decision remain pending Phase 1 gate.

---

## [0.1.6] — 2026-08-25

### Changed

- `diagnostics/wp05_live_diagnostic.py` — Removed internal AI persona names from output sections; renamed sections to "DECISIONS REQUIRING HUMAN ADJUDICATION" and "DIAGNOSTIC RECOMMENDATION"
- `docs/methodology.md` — Removed "preferred" qualifier from D-018 entry; replaced with four-dimension adjudication framework consistent with notebook Cell 30 governance and RESEARCH_LOG. No treatment has an automatic default.
- `docs/data_dictionary.md` — Filled in confirmed Phase 1 decisions: adjusted close price return via yfinance, prior-month-end VW weight construction, FF49 industry classification with SEC EDGAR SIC source and Kenneth French Siccodes49.zip crosswalk
- `README.md` — Fixed Mermaid diagram layer labels to align with the six-layer table (diagram previously labeled conflicting "Layer 2–4" while table showed "Layer 3–5"); added link to `docs/live_data_execution_handoff.md` in Current State section and navigation footer
- `CHANGELOG.md` — Added missing v0.1.4 and v0.1.5 entries; added this entry

### Rationale

Repository hardening audit before public transfer. All changes are documentation or terminology corrections. No research decisions changed, no methodology changed.

---

## [0.1.5] — 2026-08-25

### Added

- `diagnostics/wp05_live_diagnostic.py` — Standalone live data diagnostic script for WP-05 Phase 1 / Sprint B. Produces four diagnostic charts and a text report covering: data coverage, VW weight distribution, D-018 Option A vs B decomposition comparison, and D-020 coverage range diagnostic. Requires local network access (Yahoo Finance, SEC EDGAR, Kenneth French Data Library). Caches intermediate data. Does not execute inside the cloud environment.
- `docs/live_data_execution_handoff.md` — Complete setup and execution guide for local notebook run. Documents D-018 and D-020 decision capture points with four-dimension adjudication framework for D-018. Clarifies that WP-05 output is replication validation, not H1 evidence.

### Changed

- `notebooks/02_historical_replication.ipynb` — Cell 30: replaced misleading threshold guidance (< 2% / > 5% median relative diff) with four-dimension D-018 adjudication framework; no treatment has an automatic default. Cells 4, 5, 18, 22, 24, 28, 42: replaced deprecated `axis='columns'` with `axis=1` (pandas ≥ 2.0 compatibility). Cells 28, 42: added Option A structural note clarifying that `pandas sum(skipna=True)` is algebraically equivalent to treating NaN returns as zero — NOT implicit renormalization — and that effective weight sum < 1 on missing-data days.

### Methodology Registrations

- **Option A (valid_days) structural characterization:** pandas `R.mul(W).sum(axis=1, skipna=True)` treats missing stock returns as zero while retaining original weights. Effective weight sum on a missing-data day equals 1 minus the sum of the absent stocks' weights — less than 1. This is NOT equivalent to explicit renormalization (which would rescale remaining weights to sum to 1). mu_d is pulled toward zero relative to renormalization. Whether this inflates or deflates any given month's MKT component depends on the sign of mu_d on those days; the direction is asymmetric.
- **D-018 adjudication framework registered:** Four dimensions required — estimator construction, cross-component empirical sensitivity, universe-composition differences, missingness clustering. No automatic default authorized. Decision will be registered before Phase 2.

---

## [0.1.4] — 2026-08-25

### Added

- `diagnostics/wp05_synthetic_validation.py` — Standalone WP-05 synthetic validation script. Runs 24 known-answer tests of the CLMX variance decomposition engine against analytically derived solutions. Produces exit code 0 on full pass. Executable independently of pytest.

### Changed

- `PROJECT_CHARTER.md` — Added D-020 addendum to Section 11 (Open Design Decisions) registering provisional 2010–2024 study window. Original preregistration language preserved unchanged.
- Various — Repository hygiene pass.

### Validation

- **WP-05 synthetic validation: 24/24 PASS.** All three CLMX components (MKT, IND, FIRM) verified against analytical solutions. Decomposition identity (MKT + IND + FIRM ≈ total variance) confirmed within floating-point tolerance. Non-negativity confirmed for all components under both VW and EW weighting.

---

## [0.1.3] — 2026-08-19

### Changed

- `notebooks/02_historical_replication.ipynb` — Restructured from exploratory v0.1.2 draft (9 sections) to canonical learning-first v0.1.3 architecture (12 steps). Key changes: all function definitions consolidated in Step 12; Steps 5/6/7 now show MKT, IND, and FIRM components in separate manual steps before the full loop; weight construction promoted to standalone Step 4 with diagnostics; raw data inspection added as Step 2 (missingness heatmap, anomaly screening, D-020 coverage diagnostic); D-018 comparison implemented in Step 8 with explicit `missing_treatment` parameter flag; reconciliation/sanity checks promoted to Step 9 with per-month n_stocks chart and non-negativity assertion; limitations restructured by priority (HIGH/MEDIUM/LOWER) in Step 11.
- `RESEARCH_LOG.md` — Phase 0 completion entry added. Registered: CLMX estimator confirmation, FF49 industry classification decision, CLMX (2022) primary benchmark, Chiah (2020) secondary benchmark, D-017 accepted, D-018 open, D-019 accepted, D-020 accepted, WP-05 activation.
- `docs/methodology.md` — Added "CLMX Variance Decomposition" section with confirmed estimator formula, VW convention, FF49/SIC pipeline with snapshot-date requirement, survivorship filter as explicit architectural node, D-017/D-018 observation rules, and explicit distinction between CLMX FIRM variance and FF6-residual variance (Phase 5).
- `README.md` — Phase 0 status updated to complete; Phase 1/WP-05 noted as active.
- `src/attribution/factors.py` — `FactorAttributionResult` docstring updated to note that `residual_variance` means "unexplained by FF6 specification" — distinct from CLMX FIRM variance, which removes only market and industry components.

### Methodology Registrations

- **CLMX estimator confirmed:** Monthly variance = sum of raw squared daily return components (not demeaned, not normalized by trading-day count). Source: CLMX (2022) NBER WP 29916.
- **FF49 confirmed:** 49 industries (not 48); SIC crosswalk from Kenneth French Data Library.
- **D-017 accepted:** 10-day minimum observation threshold per stock per month.
- **D-018 open:** Complete-month (Option B) vs. valid-day (Option A) — pending overlay chart review.
- **D-019 accepted:** VW primary; EW deferred to post-validation.
- **D-020 accepted (provisional):** 2010–2024 primary; 2005–2024 conditional on Phase 1 diagnostics.
- **WP-05 activated:** Historical replication workstream, Phase 1.

### Research State

Phase 0 literature reconnaissance complete. H1 remains genuinely open — the pre-2001 secular trend (CLMX 2001) did not persist cleanly after approximately 2001 (CLMX 2022, Chiah 2020). Results of the 2010–2024 replication are not yet known. No hypothesis testing has occurred.
