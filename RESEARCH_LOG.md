# Project Parallax — Research Log

*A running record of research decisions, hypothesis evolution, methodological changes, and findings as they emerge.*

Evidence and interpretation are kept explicitly separate throughout this log.

---

## 2026-08-18 — Project Initiation

**Status at entry:** Pre-analysis. No substantive hypothesis testing has occurred.

### Originating Observation

Large positive and negative moves in individual equities appear increasingly common, while securities grouped within the same sector, industry, or investment theme sometimes fail to move together as uniformly as expected. This observation motivates the research question but does not constitute evidence for it.

### Research Question Registered

Has the share of individual-security return variation not explained by common systematic exposures increased over time within at least some areas of the U.S. equity market?

### Hypotheses Registered (Pre-Analysis)

**H1 — Rising Security-Specific Importance**
Within at least some U.S. equity sectors or industries, the share of security-level return variation remaining after systematic controls has increased over time.

Primary operationalization: residual or specific variance as a proportion of total security-level variance after controlling for specified systematic exposures.

**H0 — No Meaningful Structural Increase**
After appropriate controls, there is no persistent or economically meaningful increase in security-specific importance across the U.S. equity market or relevant subgroups. H0 is an acceptable and successful project outcome.

Sub-hypotheses H1a (structural expression through dispersion/correlation), H1b (portfolio attribution expression), H1c (explanation test bridging Brinson and factor attribution), H2 (sector heterogeneity), and H3 (regime dependence) are documented in the Project Charter.

### Competing Explanations Registered (Pre-Analysis)

Four explanations are active before any testing begins:

- **A — Genuine idiosyncratic divergence:** firms increasingly behave differently for firm-specific reasons.
- **B — Classification failure:** sector/industry labels increasingly group companies with systematically different exposures.
- **C — Regime effects:** the apparent trend is cyclical or conditional, not secular.
- **D — Availability bias:** the original observation is wrong; visible large moves create an illusion of structural change.

The project must be capable of distinguishing among these explanations, not merely identifying which one is consistent with the data.

### Open Decisions (Registered Unresolved)

The following decisions are intentionally unresolved. They will be locked before Phase 2 hypothesis testing begins.

- **Return frequency:** not yet selected. Will be determined by methodological requirements, literature precedent, and statistical properties of the specific measures used.
- **Historical horizon:** not yet selected. Will be determined by data quality, bias severity, factor-data availability, and regime coverage.
- **Universe:** S&P 500 is the provisional prototype universe. Adequacy depends on Phase 1 survivorship-bias and constituent-coverage validation.

### Analytical Baseline Registered

- **Factor model baseline:** Fama-French Five Factors + Momentum (FF6), sourced from the Kenneth French Data Library.
- **Brinson validation approach:** controlled synthetic portfolios with known expected attribution will be constructed and validated before the engine is applied to empirical portfolios.

### Work Authorized

**Phase 0 — Literature Reconnaissance:** In progress.
Priority topics include: idiosyncratic volatility trends and the Campbell, Lettau, Malkiel, and Xu (2001) literature and subsequent evidence; cross-sectional equity dispersion; within-sector and within-industry correlation; Brinson attribution methodology; factor attribution and Brinson versus factor attribution comparisons; sector-classification explanatory power.

**Phase 1 — Data Feasibility:** In progress.
Initial data source: Yahoo Finance / yfinance. Survivorship bias identified as a first-class analytical risk. Escalation path if free data proves inadequate: Sharadar / Nasdaq Data Link.

### Research Standard

Every material analytical test will record its question, hypothesis, null hypothesis, measurement approach, data used, assumptions made, expected evidence, falsifying evidence, method, result, interpretation, alternative explanations, limitations, confidence level, and next question. Evidence and interpretation will be explicitly separated throughout.

### Note on This Entry

This entry exists to create a public record that hypotheses were registered, competing explanations were enumerated, and open methodological decisions were documented before substantive empirical testing began. The governing principle: the project begins with an intuition, but the intuition does not get a vote once the evidence arrives.

---

## 2026-08-19 — Phase 0 Complete / Phase 1 Active (WP-05)

**Status at entry:** Phase 0 literature reconnaissance complete. Phase 1 historical replication underway (WP-05 activated). No hypothesis testing has occurred.

### Phase 0 Findings Registered

**Literature reconnaissance completed.** Primary and secondary benchmarks identified and reviewed. Key finding from the literature: the secular rise in idiosyncratic volatility documented by CLMX (2001) over 1962–1997 did not persist cleanly after approximately 2001. H1 remains genuinely open as a question under investigation — it is not an assumed finding.

**CLMX variance estimator confirmed.** Source: Campbell, Lettau, Malkiel & Xu (2022), NBER WP 29916, Figure notes 1–4. Monthly variance = sum of raw squared daily return components within each month. Returns are NOT demeaned before squaring. Monthly totals are NOT divided by trading-day count. This estimator is confirmed by the original authors' own restatement.

**FF49 industry classification confirmed.** Fama-French 49 industries (not 48). Confirmed from CLMX (2001) paper text. Classification via SIC code crosswalk from the Kenneth French Data Library (Siccodes49.zip). SIC codes sourced from SEC EDGAR public API. Software/hardware split in FF49 is relevant for modern S&P 500 composition.

**Post-2001 directional benchmark registered.** Campbell, Lettau, Malkiel & Xu (2022), NBER WP 29916, "Idiosyncratic Equity Risk Two Decades Later." Figures 2, 3, and 4 are the primary directional comparison targets for Project Parallax's 2010–2024 replication. Finding: no persistent secular increase in FIRM variance share post-2001; market and industry components elevated post-crisis.

**Secondary robustness benchmark registered.** Chiah, Gharghori & Zhong (2020), *Critical Finance Review*, "Has Idiosyncratic Volatility Increased? Not in Recent Times." Independent (non-CLMX-author) replication through 2016–2017. Confirms no persistent post-2001 increase. Useful as adversarial check on CLMX (2022) because it is methodologically independent.

### Design Decisions Registered

**D-017 — Minimum observation threshold: ACCEPTED**
Minimum 10 valid daily return observations per security per month. Stocks with fewer than 10 valid days are excluded from that month's decomposition. This is a Parallax design choice; it is NOT stated in the original CLMX (2001) methodology. Documented as a deviation in notebook Step 11.

**D-018 — Missing data treatment: OPEN**
Two options are under evaluation:
- Option A (valid-day inclusion): include stocks with ≥ 10 valid days; stock may be missing on some days within the month.
- Option B (complete-month completeness): include only stocks valid on every trading day.
The structural difference is that Option A allows day-by-day portfolio composition changes within a month; Option B fixes the portfolio for the month. Decision requires reviewing the FIRM variance overlay chart from notebook Step 8 before proceeding. Will be registered before Phase 2.

**D-019 — Weighting convention: ACCEPTED**
Value-weighted (VW) primary. Equal-weighted (EW) deferred until VW series is validated. Consistent with CLMX (2022) which reports both; VW is the base case.

**D-020 — Study window: ACCEPTED (provisional)**
Primary window: 2010–2024. May extend to 2005–2024 pending Phase 1 coverage diagnostics (notebook Step 2). Extension decision based on ticker coverage rate and survivorship-bias severity in the 2005–2009 period, not on which horizon produces more favorable results.

### Work Product

`notebooks/02_historical_replication.ipynb` — Restructured to v0.1.3 canonical 12-step learning-first architecture. All function definitions consolidated in Step 12. Steps 1–11 show computations inline. D-018 comparison implemented in Step 8 with explicit parameter flag. Raw data inspection promoted to Step 2. Weight construction promoted to standalone Step 4. Limitations structured by priority in Step 11.

### Note on AI Assistance

Literature reconnaissance for Phase 0 was supported by AI-assisted search. All methodology confirmations trace to primary sources: CLMX (2001) original paper, CLMX (2022) NBER WP 29916 (Figure notes for estimator confirmation), and the Kenneth French Data Library (FF49 crosswalk). AI output is not treated as empirical evidence; decisions registered here are grounded in those primary sources.

---

## 2026-08-25 — WP-05 Validated / Live Execution Handoff Issued / Repository Hardening

**Status at entry:** Phase 1 active. WP-05 synthetic validation complete. Live data execution not yet run. No empirical results exist.

### WP-05 Synthetic Validation Complete

**24/24 synthetic tests PASS.** The CLMX three-component variance decomposition engine (MKT, IND, FIRM) has been validated against 24 analytically derived known-answer cases, spanning: single-stock / multi-stock scenarios; VW and EW weighting; MKT-only, IND-only, and FIRM-only variance allocations; multi-industry and multi-stock-per-industry cases; decomposition identity (MKT + IND + FIRM ≈ total) to floating-point tolerance; and non-negativity of all components. Validation implemented in `diagnostics/wp05_synthetic_validation.py` (standalone, no pytest dependency). This validates the mathematical implementation; it does not constitute empirical evidence about H1.

### Work Products Committed

- `diagnostics/wp05_live_diagnostic.py` — Standalone script for local live-data Sprint B evidence. Requires local network access to Yahoo Finance, SEC EDGAR, and Kenneth French Data Library. Produces four diagnostic charts and a text report. Run locally before notebook execution.
- `docs/live_data_execution_handoff.md` — Complete local execution guide. Documents D-018 and D-020 decision capture points, execution order, and what to record after the run.

### Option A Structural Characterization (registered)

The valid-day inclusion treatment (Option A) uses `pandas R.mul(W).sum(axis=1, skipna=True)`. This is algebraically equivalent to treating each absent stock's return as 0.0 on its missing days while retaining all original weights. The effective contributing weight sum on a missing-data day equals 1 minus the sum of the absent stocks' weights — strictly less than 1. This is NOT implicit renormalization: explicit renormalization would rescale the remaining weights to sum to 1, producing a higher mu_d (when the market is positive) than what skipna returns. Under Option A, mu_d is pulled toward zero relative to renormalization. The direction of any resulting MKT bias is asymmetric and month-specific, depending on the sign of mu_d on missing-data days. This is the structural definition of Option A, not a bug. Documented in notebook Cells 28 and 42 and in the diagnostic script docstring.

### Notebook Governance Updates (Cell 30)

The D-018 overlay comparison in notebook Cell 30 previously contained threshold guidance ("< 2% median relative diff → prefer Option B") that implied an empirical shortcut to D-018 adjudication. This guidance has been replaced with a four-dimension adjudication framework requiring: (1) methodological defensibility, (2) empirical sensitivity across MKT, IND, and FIRM separately, (3) universe-composition analysis, and (4) missingness clustering assessment. No treatment has an automatic default. D-018 remains OPEN; resolution requires the live empirical overlay from notebook Step 8.

### D-018 Governance Language Corrected

`docs/methodology.md` previously described Option B as "preferred" under the D-018 entry. This language has been removed. No treatment is preferred in advance of the live-data adjudication. The D-018 entry now states the four-dimension framework and the requirement for explicit rationale in `RESEARCH_LOG.md` at time of resolution.

### Next Question

Run `notebooks/02_historical_replication.ipynb` locally against live Yahoo Finance / EDGAR / French Library data. Execute Steps 1–12 in order. At Step 2: record coverage diagnostic evidence for D-020. At Step 8: adjudicate D-018 across the four dimensions. Record results in `RESEARCH_LOG.md` per handoff document. WP-05 Phase 1 live pass pending.

---

*Results will be appended as phases complete.*

---

## 2026-09-12 — WP-05 Phase 1 Live Execution Complete / D-018 and D-020 Resolved / Phase 1 Hardening

**Status at entry:** Phase 1 live execution complete. D-018 and D-020 resolved. No hypothesis testing has occurred. WP-05 output is replication validation, not H1 evidence.

### WP-05 Phase 1 Live Execution

The live historical pass of the CLMX variance decomposition was executed locally against Yahoo Finance, SEC EDGAR, and Kenneth French Data Library data following the handoff documented in `docs/live_data_execution_handoff.md`. All 180 calendar months (January 2010 – December 2024, primary window, D-020 resolved) were decomposed.

**Data coverage (primary window):**
- Price matrix: 5,032 days × 503 tickers (2005-01-03 to 2024-12-30, per yfinance exclusive-end convention — see Endpoint Note below)
- Return matrix (primary window): 3,773 trading days × 503 tickers (2010-01-04 to 2024-12-30)
- 503 tickers classified across FF49 industries via SEC EDGAR SIC codes and Kenneth French Siccodes49.zip crosswalk

**Execution issues encountered and resolved during live run:**

*FF49 parser repair:* The initial FF49 SIC-to-industry crosswalk parser failed to handle contiguous SIC ranges without whitespace delimiters in the raw Siccodes49.txt file. The parser was repaired to recognize all range formats. This is a data ingestion fix; it does not affect the CLMX methodology.

*Wikipedia User-Agent requirement:* The S&P 500 constituent scraper (used to build the ticker list from the Wikipedia historical table) required an explicit `User-Agent` header to avoid HTTP 429 rate-limiting. Added to the ingestion pipeline. This is a data retrieval fix; it does not affect universe selection methodology — the constituent list is derived from the same public source.

*Dependency gaps discovered:* `lxml>=4.9.0` (required for Wikipedia HTML parsing) and `pyarrow>=12.0.0` (required for `.parquet` cache reads) were missing from `requirements.txt`. Added. No methodology impact.

*v1 diagnostic issues:* The initial `wp05_live_diagnostic.py` output (`wp05_qt_audit.txt` v1) contained a docstring `SyntaxWarning` (unescaped backslash) and a formatting anomaly in the q_t audit output. A corrected v2 was produced and confirmed correct.

### D-020 Resolved — Study Window: 2010–2024

The 2005–2009 extended window was evaluated using the Phase 1 coverage diagnostic (notebook Step 2). Ticker coverage in the 2005–2009 period fell below the 85% quality threshold in multiple months. D-020 is **RESOLVED: 2010–2024 (180 months)**. The extended window 2005–2009 fails the coverage gate and is excluded from all Phase 1 analyses. This decision was based on the coverage diagnostic, not on which window produces more favorable empirical results.

### D-018 Resolved — Missing Data Treatment: Option B (complete_month)

D-018 was adjudicated across four dimensions: (1) methodological defensibility, (2) empirical sensitivity across MKT, IND, and FIRM, (3) universe-composition differences, and (4) missingness clustering. **D-018 is RESOLVED: Option B (complete_month) is canonical for Phase 1.** Under Option B, a stock-month is eligible only when the stock has returns on every cached trading day for that month. This is the methodologically defensible choice: it maintains a fixed within-month portfolio and avoids the asymmetric zero-imputation behavior documented for Option A (see Option A characterization in 2026-08-25 entry and Option A Latent Defect section below).

**Empirical confirmation — q_t audit:**
The daily weight audit (`wp05_qt_audit.txt` v2) confirmed that q_t = 1.0 (within tolerance 1e-9) on all 3,773 trading days under both Option A and Option B. There are 45 ticker-months present in Option A but not Option B (A-exclusive). All 45 A-exclusive ticker-months have zero prior-month-end market-capitalization weight. Consequently, the CLMX component totals (MKT, IND, FIRM) differ by less than 1e-15 across all 180 months between the two options. This confirms that D-018 has no material effect on the Phase 1 empirical result for this cached dataset, and that Option B is the methodologically appropriate choice without requiring a numerical tradeoff.

### WP-05 Phase 1 Replication Results (replication validation — not H1 evidence)

The following are Phase 1 CLMX replication statistics. They are presented as replication validation output under D-018 Option B (canonical), D-020 (2010–2024). They are NOT evidence about H1 and do not constitute hypothesis testing. Phase 2 hypothesis testing has not been authorized and has not begun.

**FIRM variance share — two distinct statistics (must not be conflated):**

- **Ratio of period sums:** FIRM / (MKT + IND + FIRM), computed as a ratio of the summed monthly components across all 180 months. **39.9490%.** This is the appropriate statistic when the question concerns the total-period composition of aggregate variance.

- **Mean of monthly ratios:** Arithmetic mean of the monthly FIRM / (MKT + IND + FIRM) ratio, computed month-by-month then averaged. **46.3215%.** This is appropriate when the question concerns the typical monthly composition and is upward-biased relative to the ratio-of-sums because months with low total variance have disproportionately high FIRM share.

Neither statistic is reported as evidence for or against H1. Both are replication statistics for internal documentation.

**Limitations (registered):**

- **Survivorship bias:** The ticker universe is based on current S&P 500 constituent membership projected backward. This is NOT historical point-in-time membership. Securities that entered and exited the S&P 500 during 2010–2024 without surviving to the current constituent list are excluded. The direction and magnitude of any resulting bias on FIRM variance share have not been empirically established for this dataset. No directional claims are made.
- **Universe scope:** Approximately 503 tickers derived from current S&P 500 membership. The CLMX (2001) study covered a broader universe (NYSE, AMEX, Nasdaq) without the S&P 500 membership filter.
- **Data source:** Yahoo Finance adjusted close prices via yfinance. Data quality events (adjustments, delistings, price anomalies) are not comprehensively validated beyond the Phase 1 anomaly screening (50% threshold).

### Option A Latent Defect — Discovered and Repaired (September 2026)

A latent defect was discovered in `decompose_month_clmx()` within `wp05_live_diagnostic.py`. The defect affected only Option A (valid_days) code paths; Option B is unaffected.

**Defect:** The FIRM computation inconsistently combined two imputation conventions. The market return (mu_d) and industry return (r_j) were computed using `pandas sum(skipna=True)`, which treats NaN returns as zero. The security-level residual (eps) was computed as `R[ticker] - r_j`, where R[ticker] is NaN on the stock's missing days. Because `(NaN ** 2).sum()` silently drops NaN terms, FIRM was understated by `Σ_j W_j × w_ij × (r_j,d)²` for each positive-weight ticker missing on day d.

**Impact:** Under Option B (canonical), R has no NaN values by construction, so the defect had zero impact on any Phase 1 empirical result. The q_t audit further confirmed that all 45 A-exclusive ticker-months had zero prior-month-end weight, making the defect numerically inert even if Option A had been run.

**Fix:** Added `R_filled = R.fillna(0.0)` after weight normalization. mu_d, r_j, and eps are all computed from `R_filled` consistently. Both imputation conventions produce the same result (explicit fillna versus skipna=True) for mu_d and r_j; the fix brings eps into alignment.

**Regression test:** `tests/test_clmx.py` documents the defect, the fix, and the analytical expectations across 8 test cases using a synthetic 2-stock / 2-day case with known analytical solutions (defective FIRM = 0.00013440; correct FIRM = 0.00019200; gap = −5.76×10⁻⁵). The test suite is standalone — no yfinance or matplotlib imports.

The same fix was applied to the inline `decompose_month()` and `clmx_decompose_month()` functions in `notebooks/02_historical_replication.ipynb`.

### pct_change Fill Policy Audit

All canonical return-construction paths now use `pct_change(fill_method=None)` to prevent implicit forward-filling of prices across trading gaps. Verified in: `wp05_live_diagnostic.py` (line 597), `wp05_daily_weight_audit.py` (line 222), and `notebooks/02_historical_replication.ipynb` (cell-step3-prices). Implicit price forward-fill would create artificial near-zero returns on the first day after a data gap; `fill_method=None` propagates NaN instead, which is then handled explicitly by the Option B eligibility filter.

### Endpoint Note — 2024-12-30 vs 2024-12-31

`STUDY_END = '2024-12-31'` is the configured end date. `yf.download(..., end='2024-12-31')` treats `end` as exclusive (Python range convention), returning trading sessions through and including 2024-12-30 but not 2024-12-31 itself. December 31, 2024 (Tuesday, NYSE open) is therefore not included in the price cache. The 180-month decomposition covers January 2010 through December 2024 in full; December 2024 comprises the 21 trading sessions from December 2 through December 30, 2024. The cache is internally consistent; the final session is the last yfinance-returned trading day, not a gap. D-020 is not reopened.

### G-Zephy Phase 1 Hardening Assignment

Following Phase 1 live execution and D-018/D-020 resolution, a comprehensive Phase 1 Hardening pass was conducted to bring the public repository into alignment with completed Phase 1 state. The hardening covered: Option A defect repair and regression test, pct_change audit, dependency updates (lxml, pyarrow), FIRM share disambiguation, survivorship language correction, README status update, endpoint documentation, and 4-commit public release sequence. See CHANGELOG v0.2.0 for the complete change record.
