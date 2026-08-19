# Changelog

All material changes to the Project Parallax research design, methodology, data strategy, and repository structure are documented here.

A change is "material" if it affects hypotheses, operationalizations, universe, dataset, factor model, attribution methodology, return frequency, research horizon, or project scope. Exploratory extensions and code improvements are noted but do not require the same level of documentation.

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

## [0.1.1] — 2026-08-19

### Changed

- `PROJECT_CHARTER.md` Section 9: renamed "Portfolio C — Combined Active" to "Portfolio C — Combined Effects" to remove unintended active-portfolio connotation
- `PROJECT_CHARTER.md` Section 4 (H1): added literature context note acknowledging that the Campbell-Lettau-Malkiel-Xu secular trend did not persist cleanly post-2001; clarified that H1 is a directional hypothesis under investigation, not an assumed finding
- `src/attribution/factors.py`: added explicit model-dependence caveat clarifying that residual/specific return means "unexplained by this specification," not "inherently firm-specific"
- `src/validation.py`: softened "recommended handling" to "suggested data handling guidance"
- `docs/methodology.md`: added "Residual Return — Model Dependence" section; added "Primary comparative question" to Brinson section foregrounding the Brinson/factor comparative research output

### Rationale

Language audit and literature-informed refinement following Phase 0 preliminary findings. No hypothesis changes. No operationalization changes.
