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
