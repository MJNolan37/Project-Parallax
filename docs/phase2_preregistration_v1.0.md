# Project Parallax Phase 2 Preregistration v1.0

*Structural Change in Firm Specific Return Variation 2010 to 2024*

<!-- CONVERSION-NOTE-BEGIN -->
> **Format conversion. The DOCX governs.**
> Source: `Project-Parallax-Phase-2-Preregistration-v1.0.docx`, SHA-256 `12699fd7c0f0793602ef5620628d61b45140582fb82781b5f92149ce1a410ba7`. Where this file and the DOCX differ, the DOCX controls.
> Text is carried over unchanged. Formatting changes only: section headings are one level below the title, and the page footer is omitted.
> Converted 2026-10-11 with pandoc 3.1.3 by the project's AI build assistant. Verified by a normalized paragraph-by-paragraph comparison against the DOCX (all paragraphs identical, in order). Not yet reviewed by the project owner.
> The freeze date below is the document's own statement. This repository's commit date records only when the specification became public; the dated freeze history is kept in the project's decision record, not in this repository.
<!-- CONVERSION-NOTE-END -->

**Specification freeze:** 23 September 2026 **Status:** Phase 2.1 specification frozen; implementation validation authorized. **Execution gate:** No Project Parallax empirical H1 or H2 execution until the synthetic and known answer validation suite passes and Matt/G review the validation evidence. Any change to this statistical specification requires a documented amendment with rationale and provenance before empirical execution.

This preregistration fixes the Phase 2 research questions, estimands, decision rules, outputs, and limitations before inspection of the empirical Phase 2 H1/H2 series. Phase 2.1 covers the primary full sample structural change analysis, a raw share sensitivity, and H2 sector heterogeneity conditional on H1. Phase 2.2 extraordinary event sensitivities and H3 recurring regime analysis have separate gates. This document supersedes the Phase 2 preregistration v0.1 H2 inference section wherever the final full covariance repair differs.

## 1 Research questions and scope

**H1, confirmatory.** Does the aggregate market wide FIRM share exhibit a statistically detectable persistent structural level change over January 2010 through December 2024?

**H2, confirmatory and conditional.** If H1 detects one or two break episodes, do the magnitudes of the FIRM share level shifts differ across Fama French 12 sectors at the H1 identified break dates? H1 finding zero breaks ends H2 without a test.

**H3, exploratory and deferred.** Whether recurring high and low FIRM share states exist is reserved for separately authorized regime analysis. H1 break detection does not establish recurring regimes.

The no peeking rule covers the monthly transformed path, the raw FIRM share path, sector paths, and intermediates used for method selection. Only synthetic and known answer data may be used for implementation validation before the execution gate opens.

## 2 Data universe and primary outcome

The study window is January 2010 through December 2024 inclusive, nominally 180 monthly observations. D-020 fixes this horizon. Monthly observations use the final available trading day in each calendar month. December 2024 remains a valid month if at least ten trading days of daily return data exist; a 31 December price observation is not required. Phase 1 Option B complete_month missing treatment is fixed by D-018.

The aggregate input is the Phase 1 canonical data/clmx_monthly_decomp_opt_b.csv, produced under Option B by diagnostics/wp05_live_diagnostic.py. The universe is current S&P 500 constituents projected backward. The CLMX components are monthly MKT, IND, and FIRM variance components based on raw squared daily returns, without demeaning or division by the trading day count, as implemented in Phase 1. FIRM removes the market and FF49 industry components; it is not a measure of variance free of every systematic factor exposure.

Define the monthly FIRM share and primary response as

> s_t = FIRM_t / (FIRM_t + MKT_t + IND_t)

z_t = log(s_t / (1 - s_t)) = log(FIRM_t / (MKT_t + IND_t)).

H1 inference uses z_t. Report segment means and changes in log odds and back transformed share units. Before transformation, require 0 \< s_t \< 1 for every month. An exact zero or one is a data quality failure and halts execution pending investigation. For 0 \< s_t \<= 10^-6, set s_t = 10^-6; for 1 - 10^-6 \<= s_t \< 1, set s_t = 1 - 10^-6. Record each original value, month, and total number of adjustments. No extra sensitivity is triggered by a cap.

The Phase 1 FF49 SIC crosswalk vintage and the FF12 SIC crosswalk used for H2 are fixed by checksums before execution. H2 requires stock level daily returns, market capitalizations, and FF49 assignments from Phase 1 intermediates or faithful reconstruction. The aggregate CSV alone cannot produce H2.

## 3 H1 structural change model and decision

Fit a Bai Perron pure intercept shift model to z_t: z_t = mu_j + epsilon_t within segment j, with ordered break dates and at most two breaks. The minimum segment length is h = floor(0.15 T) = 27 months at T = 180, applied to every segment and bootstrap replicate. A three break model is outside Phase 2.

First perform UDmax at 5% across the allowed one and two break alternatives. If it does not reject, select **Conclusion State 1**, no statistically detected persistent level shift. If it rejects, use sequential supF(2\|1) at 5%: non rejection selects **Conclusion State 2**, one detected shift; rejection selects **Conclusion State 3**, two detected shifts. Report the statistics and critical values. Break dates and analytic break date confidence intervals come from R strucchange through rpy2; the wrapper does not recreate Bai Perron test statistics. Record exact R and package versions.

The frozen H1 dependence recipe is the Andrews quadratic spectral (QS) kernel, automatic AR(1) bandwidth selection, and VAR(1) prewhitening, applied segment wise to residuals from the intercept only fit. Apply the same recipe in the primary analysis, bootstrap replications, and raw share sensitivity. The implementation validation suite must compare a synthetic AR(1) series with rho = 0.5, T = 100 against R sandwich to at least four significant figures.

Analytic break date intervals describe timing uncertainty. They are distinct from the bootstrap intervals for shift magnitude. The 27 month minimum is an identification floor within this sample, not proof of permanence.

## 4 H1 bootstrap and uncertainty reporting

Use a circular block bootstrap with fixed L = floor(T^(1/3)) = 5 for T = 180, B = 1,999 replications, and master seed 20260923. The block length is a transparent conventional approximation, independent of the observed series and H1 HAC bandwidth. The H1 stream is numpy.random.default_rng(SEED + 0); the raw share sensitivity uses SEED + 2. SEED + 1 remains reserved and unused because H2 has no bootstrap. Pass RNG objects explicitly; do not use global random state.

Each replicate resamples a length T circular block series and reruns the complete frozen H1 selection procedure with the same two break cap, trimming, significance levels, and HAC recipe. Report counts and proportions selecting zero, one, and two breaks across all 1,999 replicates, including when the primary result selects zero. This is the model selection stability diagnostic.

For each detected primary shift, the 95% percentile interval targets magnitude conditional on a replicate recovering the primary break count. Match comparable breaks chronologically, first to first and second to second. Replicates with a different break count contribute to the frequency table but not the magnitude interval; no shift is filled with zero. If fewer than 200 replicates recover the primary break count, report the conditional magnitude interval as **not reliably estimable**, with the exact comparable count. No substitute interval is introduced, and the H1 detection result and analytic break date intervals remain unchanged. The threshold of 200 is a preregistered practical Monte Carlo adequacy floor, not a sharp scientific boundary.

The conditional percentile interval does not combine break existence, break timing, and break magnitude uncertainty into a single claim. Its selection conditioning is a known limitation.

## 5 H1 result language

**State 1:** Report no statistically detected persistent level shift under this procedure, the UDmax statistic and critical value, the no break segment mean, and bootstrap break count frequencies. This does not establish that FIRM share was constant.

**State 2:** Report the H1 break date and analytic date interval; two segment means; the shift in log odds and share units; its analytic HAC standard error and conditional bootstrap interval or failure flag; and break count frequencies. Proceed to H2 at the H1 date.

**State 3:** Report both H1 dates and analytic date intervals; three segment means; both consecutive shifts with their analytic standard errors and conditional bootstrap intervals or failure flags; and break count frequencies. Proceed to the joint two episode H2 test at those H1 dates.

Wide date intervals, unstable bootstrap break counts, a missing conditional magnitude interval, and raw share disagreement qualify interpretation without changing the primary selection rule. If fewer than half of bootstrap replicates recover the primary count, report that sensitivity explicitly. Do not call H1 proven, confirmed, or permanent; do not equate CLMX FIRM with all idiosyncratic risk; do not infer causation from a break date's coincidence with an event; and do not claim this procedure is uniquely correct.

## 6 H2 sector series and conditioning

FF12 is the confirmatory sector taxonomy. For each sector and month, recompute CLMX within that sector using Phase 1 Option B and at least ten valid daily return days. Normalize valid stock market capitalization weights to sum to one within the sector month. Use FF49 subclasses within the sector for the IND component. Define z\_(g,t) = log(FIRM\_(g,t) / (MKT\_(g,t) + IND\_(g,t))), using the sector's own denominator. A sector month with fewer than five valid data stocks is missing; five is a fixed practical degeneracy guard rather than an optimal statistical threshold. Report missing month counts by sector.

H2 uses the break date or ordered pair of dates selected by H1. It does not search for a new sector system date, synchronize sectors with a pretest, or run independent sector break searches. A sector is eligible only if it has at least one non missing observation in every H1 segment required for its episode shifts. Let G' be the number of eligible sectors. If G' \< 6, report **insufficient sector coverage; H2 not computed**. The normal case has G' = 12.

At the fixed H1 date or dates, calculate each eligible sector's mean in each segment using its non missing months. With one break, Delta_g = mu\_(g,2) - mu\_(g,1). With two breaks, Delta\_(g,1) = mu\_(g,2) - mu\_(g,1) and Delta\_(g,2) = mu\_(g,3) - mu\_(g,2).

## 7 H2 full covariance estimator

Estimate the full covariance of the sector shift vector by QS HAC on time indexed score vectors. The H2 multivariate estimator does **not** use VAR(1) prewhitening: a 12 variable VAR(1) would require 144 slope coefficients from about 180 months. This is an explicit H2 departure from the H1 recipe. It allows serial dependence and contemporaneous cross sector covariance without an equicorrelation or correlation sign assumption.

For one break, let epsilon\_(g,t) be the residual from sector g's mean in the H1 segment containing month t, and let T\_(g,k) count non missing sector months in segment k. Set v\_(g,t) = -epsilon\_(g,t)/T\_(g,1) before the break and +epsilon\_(g,t)/T\_(g,2) after it. Set that sector's score to zero when its month is missing. Stack all eligible sector scores into v_t.

For two breaks, create two score coordinates per eligible sector. Episode 1 has weights -1/T\_(g,1), +1/T\_(g,2), and zero across segments 1, 2, and 3. Episode 2 has weights zero, -1/T\_(g,2), and +1/T\_(g,3). Multiply each applicable weight by its within segment residual; missing sector months contribute zero. Stack episode 1's G' scores and episode 2's G' scores into a 2G' vector each month. The shared middle segment enters the two episode scores with opposite signs, so its cross episode covariance is represented directly within the HAC estimator.

For either score vector, form Gamma(h) = sum\_(t=h+1)^T v_t v\_(t-h)', with **no extra division by T**, because segment count factors are already inside each score. Estimate Sigma = Gamma(0) + sum\_(l=1)^B_T k_QS(l/B_T)\[Gamma(l) + Gamma(l)'\], where k_QS(x) = (25/(12 pi^2 x^2))\[sin(6 pi x/5)/(6 pi x/5) - cos(6 pi x/5)\]. For each scalar sector or sector episode score, apply the frozen Andrews AR(1) automatic bandwidth rule, B\_(T,g) = \[4 rho_g^2/(1-rho_g^2)^2\]^(1/5) T^(1/5). Use one HAC bandwidth B_T = max(1, max_g B\_(T,g)), or the maximum over sector episode coordinates for two breaks. If a segment has fewer than three usable observations for AR(1) estimation, assign that coordinate bandwidth one. The same missing score and bandwidth rules apply in validation and execution.

The estimated covariance is G' x G' with one H1 break and 2G' x 2G' with two. Report sector shift estimates and individual diagonal HAC standard errors. The full off diagonal structure is used for the confirmatory test.

## 8 H2 joint Wald test and failure states

For one H1 break, let Delta contain the G' sector shifts. Construct an (G'-1) x G' contrast matrix R with row j equal to e\_(j+1)' - e_1'. The null is that all eligible sectors have the same shift at the H1 date. Compute W = (R Delta)'(R Sigma R')^(-1)(R Delta). Use the asymptotic chi squared reference with G'-1 degrees of freedom at 5%; with twelve sectors, there are eleven restrictions and the critical value is 19.68.

For two H1 breaks, stack the first and second episode shifts into a 2G' vector and set R_joint = block_diag(R, R). The null allows the two episodes to have different common shifts but requires equality across sectors within each episode. Compute the same Wald quadratic form with R_joint and the full stacked covariance, including cross episode blocks. Use 2(G'-1) degrees of freedom at 5%; with twelve sectors, there are 22 restrictions and the critical value is 33.92. This is one joint H2 test, not two separately added tests. There is no H2 bootstrap or finite sample F adjustment.

Before calculating either Wald decision, form the contracted covariance M = R Sigma R' or R_joint Sigma_joint R_joint'. Inspect its eigenvalues and kappa(M) = lambda_max/lambda_min. If M is singular, non positive definite, or kappa(M) \> 10^8, report **H2 Wald test not computable because the estimated covariance is singular or ill conditioned**. Report the condition number where defined, full eigenvalue spectra for M and Sigma, the HAC bandwidth, and non missing sector month counts by segment. Do not use a ridge, Tikhonov adjustment, diagonal approximation, bootstrap fallback, or another test. Retain sector shifts and diagonal HAC standard errors as descriptive results; H1 is unaffected.

When the Wald test is computable, report the statistic, degrees of freedom, 5% critical value, decision, eligible sectors, break dates, and sector shifts. Non rejection means the procedure did not detect sector heterogeneity; it does not prove identical shifts. Rejection supports heterogeneity under the conditional model. Sector rankings and individual comparisons are descriptive or exploratory, not extra confirmatory decisions. The test conditions on estimated H1 dates and does not include their uncertainty.

## 9 Sensitivities and deferred analyses

The required Phase 2.1 raw share sensitivity applies the complete H1 procedure to untransformed s_t with the same break cap, trimming, tests, dependence recipe, and separate RNG child stream. Report its conclusion state and shifts. Disagreement with z_t is interpretation context and does not overturn the primary log odds result.

The full 2010 to 2024 sample remains primary. Phase 2.2 extraordinary event windows are probes, not partitions. They must be defined from named external sources and committed before the event module runs; Phase 2.1 results may not determine the windows. The \[events\] configuration section remains empty at the Phase 2.1 freeze, and Phase 2.1 does not depend on it. A later Phase 2.2 commitment must identify the externally sourced windows and any defensible alternatives before its own execution. No single interval may be retroactively selected as the true COVID or tightening interval.

The bounded or Beta change point sensitivity and PYZ variance break test are deleted from the Phase 2.1 suite. CUSUM or MOSUM, Mann Kendall, a three break H1 model, independent sector break searches, sector synchronization pretests, and FF49 confirmatory tests are excluded. HMM or Markov switching belongs to deferred H3. Any later FF49 localization is exploratory and, if authorized, uses Benjamini Hochberg FDR at 5%; it does not change H2.

## 10 Reproducibility and implementation contract

config/phase2_spec.toml is the single committed source for analytic constants, thresholds, seeds, data checksums, and package versions. It includes the H1 and H2 rules above, H2 full covariance method and its 10^8 failure threshold, the empty \[events\] section, and the reserved FF49 FDR threshold. Analysis code must not embed competing numeric literals. Record SHA 256 checksums for the aggregate Phase 1 CSV and the FF49 and FF12 crosswalk files before empirical execution, then verify them before analytical reads. A mismatch halts the run. Pin Python dependencies in requirements-phase2-lock.txt, and record R and strucchange versions.

Analysis modules live in src/phase2/; notebooks explain and display their results, contain no independent constants, and have no committed executed output. Write deterministic machine readable results to data/phase2_h1_results.json and data/phase2_h2_results.json. The H1 record includes tests, break count and dates, date intervals, segment means, shifts, standard errors, conditional interval status, and the full bootstrap count table. The H2 record includes the H1 conditioned date or dates, eligible sectors, missingness, sector shifts, covariance diagnostics, Wald result or preregistered failure state. Same machine, inputs, configuration, and seed must produce byte identical JSON.

The implementation validation evidence is a required gate. Before any Parallax empirical H1/H2 execution, demonstrate the H1 HAC known answer comparison; synthetic break selection and bootstrap behavior; one and two break H2 contrasts, covariance and Wald dimensions; score and HAC scaling against analytical or high precision Monte Carlo covariance of known segment mean differences; and asynchronous sector missingness with zero score contributions and plausible cross sector covariance. Include a two break shared middle segment case showing the cross episode covariance enters through the stacked scores. Exercise inadequate sector coverage and singular or ill conditioned covariance failure paths. Record the fixtures, expected values, observed values, tolerances, and test results in a committed validation report. Matt/G review the evidence before lifting the empirical execution gate. A validation failure prompts an implementation correction or a formally documented specification amendment, not an unrecorded method change.

## 11 Execution gates

**Current state:** Phase 2.1 specification is frozen. Building the code and validating it on synthetic and known answer data is authorized. Empirical inspection and H1/H2 execution remain closed.

**Phase 2.1 release:** After the suite passes and Matt/G review the recorded evidence, verify committed configuration, checksums, and dependencies; then run boundary checks, H1, its bootstrap, the raw share sensitivity, and H2 only if H1 selects one or two breaks. Write and verify the machine readable outputs. A failure state is reported under its frozen rule without opportunistic substitution.

**Phase 2.2 release:** Finalize Phase 2.1 results first. Source and commit extraordinary event definitions in a timestamped configuration change before running the event module, and affirm that Phase 2.1 results did not choose those definitions. H3 requires separate authorization and is outside both Phase 2.1 and Phase 2.2.

## 12 Known limitations

The backward projected current S&P 500 universe has survivorship bias of unknown direction and magnitude. Yahoo Finance prices and SEC EDGAR SIC codes are a public data approximation, with unquantified differences from CRSP or a commercial common stock universe. The CLMX FIRM component is not synonymous with factor residual or purely idiosyncratic risk.

An abrupt intercept shift model can misdescribe gradual transitions, and at about 180 months the two break cap and 27 month minimum limit resolution near endpoints. Asymptotic H1 and H2 references can have finite sample error. Conditional bootstrap magnitude intervals omit full model selection uncertainty and can carry selection bias. H2 fixes the H1 estimated dates, so its Wald covariance does not account for break date estimation uncertainty; common timing at the aggregate dates can miss sector specific transition timing. The two break H2 covariance is 24 by 24 when all sectors qualify, and numerical failure is possible; the preregistered failure result must stand. Neither event coincidence nor a detected shift proves causation or permanence beyond December 2024.

## 13 Source control and precedence

This v1.0 integrates the 23 September 2026 Phase 2 preregistration v0.1 and final lint rulings with the later H2 full covariance repair and the Matt/G implementation validation gate. The final H2 repair supersedes v0.1's separate sector break search, diagonal inverse variance Wald statistic, claimed conservatism under positive correlations, and two episode split test. The remaining v0.1 rules continue as stated here. No Phase 2 empirical results are recorded in this preregistration.
