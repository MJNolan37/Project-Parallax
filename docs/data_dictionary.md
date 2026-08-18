# Project Parallax — Data Dictionary

*To be completed during Phase 1 Data Feasibility. This skeleton establishes the structure.*

---

## Universe

| Field | Value |
|---|---|
| Prototype universe | S&P 500 |
| Universe status | Provisional — pending Phase 1 survivorship validation |
| Constituent source | To be determined in Phase 1 |
| Point-in-time coverage | To be assessed in Phase 1 |

---

## Market Data

| Field | Value |
|---|---|
| Primary source | Yahoo Finance / yfinance |
| Return type | To be specified (total return vs. price return) |
| Return frequency | Open decision — to be registered before Phase 2 |
| Historical start | Open decision — to be registered before Phase 2 |
| Adjustment method | To be documented in Phase 1 |
| Corporate action handling | To be documented in Phase 1 |

---

## Factor Data

| Field | Value |
|---|---|
| Factor model baseline | Fama-French Five Factors + Momentum (FF6) |
| Source | Kenneth French Data Library |
| URL | https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html |
| Factors | Mkt-RF, SMB, HML, RMW, CMA, Mom |
| Frequency | Monthly (primary); daily where available |

---

## Sector / Industry Classification

| Field | Value |
|---|---|
| Classification system | To be documented in Phase 1 |
| Classification source | To be documented in Phase 1 |
| Historical classification handling | To be documented in Phase 1 |
| Reclassification monitoring | Required — tracked in validation pipeline |

---

## Data Quality Flags

The following fields will be documented for each security in the research panel:

- `coverage_start` — earliest available date in source data
- `coverage_end` — latest available date (or delisting date)
- `is_current_constituent` — whether security is in the current index
- `has_complete_history` — whether the security has continuous data for the study period
- `delisted` — whether the security was removed from exchange during study period
- `corporate_action_flags` — ticker changes, mergers, spin-offs
- `sector_reclassified` — whether the security changed GICS sector during study period

---

*This dictionary will be completed as Phase 1 pipeline development proceeds.*
