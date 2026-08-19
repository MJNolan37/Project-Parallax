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

*Results will be appended as phases complete.*
