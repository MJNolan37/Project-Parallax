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
| Return type | Adjusted close price return (dividend and split-adjusted via yfinance) |
| Return frequency | Open decision — to be registered before Phase 2 |
| Historical start | Open decision — to be registered before Phase 2 (provisional: 2010-01-01, D-020) |
| Adjustment method | Adjusted close price; no additional dividend handling applied |
| Corporate action handling | To be documented in Phase 1; ticker changes and spin-offs flagged |
| VW weight construction | Prior-month-end market-cap weights (price × shares outstanding); held fixed for calendar month (D-019 accepted) |

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
| Classification system | Fama-French 49 industries (FF49; not 48 — confirmed in CLMX 2001 paper text) |
| SIC code source | SEC EDGAR public API (historical SIC codes per company) |
| SIC → FF49 crosswalk | Kenneth French Data Library, Siccodes49.zip |
| Crosswalk retrieval | Date recorded in `SIC_SNAPSHOT_META['retrieval_date']` in notebook Step 3 |
| Modern SIC handling | Modern S&P 500 companies sometimes file under legacy SIC codes; mismatches flagged |
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
