"""
Project Parallax — WP-05 Live Data Diagnostic Script
=====================================================

Standalone script producing the evidence packet for Sprint B adjudication.
Equivalent to executing notebooks/02_historical_replication.ipynb Steps 1–8,
but callable directly from a terminal without Jupyter.

Usage
-----
    cd /path/to/project-parallax
    python diagnostics/wp05_live_diagnostic.py

All intermediate data is cached under data/ to allow re-runs without
re-fetching. The full diagnostic report is written to
data/wp05_live_report.txt and printed to stdout.

Environment requirements
------------------------
    pip install yfinance pandas numpy matplotlib requests
    (network access to Yahoo Finance, SEC EDGAR, Kenneth French Data Library)

Methodology
-----------
CLMX variance decomposition:
    r_{i,j,t,d} = mu_{t,d} + eta_{j,t,d} + eps_{i,j,t,d}
    MKT_t  = sum_d  mu_d^2
    IND_t  = sum_j  W_j * sum_d  eta_{j,d}^2
    FIRM_t = sum_j  W_j * sum_i  w_{ij} * sum_d  eps_{i,j,d}^2

Estimator: raw squared daily returns, NOT demeaned, NOT divided by trading-day
count. Confirmed: CLMX (2022) NBER WP 29916, Figure notes 1-4.
Weighting: value-weighted using prior-month-end market cap (D-019).
Industry classification: Fama-French 49 industries via SIC crosswalk (D-017).
Minimum observations: 10 valid trading days per stock per month (D-017).
Study window: 2010-2024 primary (D-020, provisional).
D-018: both Option A (valid_days) and Option B (complete_month) are run.

This script is evidence generation, not hypothesis testing.
WP-05 output is CLMX replication validation, not Parallax H1 evidence.

Commit HEAD at script authorship: 1a0bfd3 (v0.1.4)
"""

from __future__ import annotations

import io
import time
import warnings
import zipfile
import datetime
import textwrap
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

warnings.filterwarnings('ignore')

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR     = PROJECT_ROOT / 'data'
DATA_DIR.mkdir(exist_ok=True)

STUDY_START_PRIMARY   = '2010-01-01'
STUDY_START_EXTENDED  = '2005-01-01'
STUDY_END             = '2024-12-31'
MIN_VALID_DAYS        = 10       # D-017
ANOMALY_THRESHOLD     = 0.50    # 50% single-day move flag

REPORT_PATH = DATA_DIR / 'wp05_live_report.txt'

# Cache paths
FF49_CACHE      = DATA_DIR / 'ff49_sic_map.csv'
EDGAR_CACHE     = DATA_DIR / 'sp500_sic_codes.csv'
PRICES_CACHE    = DATA_DIR / 'sp500_daily_prices.parquet'
SHARES_CACHE    = DATA_DIR / 'sp500_shares_outstanding.csv'
RESULTS_B_CACHE = DATA_DIR / 'clmx_monthly_decomp_opt_b.csv'
RESULTS_A_CACHE = DATA_DIR / 'clmx_monthly_decomp_opt_a.csv'
RECON_CACHE     = DATA_DIR / 'clmx_reconciliation.csv'

# ---------------------------------------------------------------------------
# Report writer
# ---------------------------------------------------------------------------

_report_lines: list[str] = []

def log(msg: str = '', indent: int = 0) -> None:
    line = '  ' * indent + msg
    print(line)
    _report_lines.append(line)

def section(title: str) -> None:
    bar = '═' * 70
    log()
    log(bar)
    log(f'  {title}')
    log(bar)

def hr() -> None:
    log('─' * 70)

def save_report() -> None:
    REPORT_PATH.write_text('\n'.join(_report_lines))
    print(f'\nReport written to {REPORT_PATH}')


# ===========================================================================
# Section 1: FF49 SIC crosswalk
# ===========================================================================

def fetch_ff49_crosswalk() -> pd.DataFrame:
    if FF49_CACHE.exists():
        log(f'  FF49 crosswalk: loading from cache ({FF49_CACHE.name})')
        return pd.read_csv(FF49_CACHE)

    import requests
    url = 'https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/Siccodes49.zip'
    log(f'  Fetching FF49 crosswalk from French Data Library...')
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        raw = zf.read(zf.namelist()[0]).decode('latin-1')

    rows, cur_num, cur_name = [], None, None
    for line in raw.splitlines():
        parts = line.split()
        if (len(parts) >= 2 and parts[0].isdigit()
                and parts[1].isalpha() and len(parts[0]) <= 2):
            cur_num, cur_name = int(parts[0]), parts[1]
        elif len(parts) == 2 and all(p.isdigit() for p in parts):
            if cur_num is not None:
                rows.append({'sic_lo': int(parts[0]), 'sic_hi': int(parts[1]),
                             'industry_num': cur_num, 'industry_name': cur_name})

    ff49 = pd.DataFrame(rows)
    ff49.to_csv(FF49_CACHE, index=False)
    log(f'  FF49 crosswalk fetched and cached: {len(ff49)} SIC ranges.')
    return ff49


# ===========================================================================
# Section 2: S&P 500 tickers + EDGAR SIC codes
# ===========================================================================

def fetch_sp500_tickers() -> list[str]:
    import requests
    log('  Fetching current S&P 500 constituents from Wikipedia...')
    tables = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
    tickers = tables[0]['Symbol'].str.replace('.', '-', regex=False).tolist()
    log(f'  {len(tickers)} tickers retrieved (as of {datetime.date.today()})')
    return tickers


def fetch_edgar_sic(tickers: list[str]) -> pd.DataFrame:
    import requests

    if EDGAR_CACHE.exists():
        log(f'  EDGAR SIC codes: loading from cache ({EDGAR_CACHE.name})')
        df = pd.read_csv(EDGAR_CACHE, dtype={'sic': str})
        log(f'  Loaded {len(df)} rows; retrieval_date col: '
            f'{df["retrieval_date"].iloc[0] if "retrieval_date" in df.columns else "not recorded"}')
        return df

    headers = {
        'User-Agent': 'Project Parallax research mattnolan.archive@gmail.com',
        'Accept-Encoding': 'gzip, deflate',
    }
    retrieval_date = str(datetime.date.today())

    log(f'  Fetching ticker→CIK index from SEC EDGAR...')
    r = requests.get('https://www.sec.gov/files/company_tickers.json', headers=headers)
    r.raise_for_status()
    cik_data = r.json()
    ticker_to_cik = {v['ticker']: str(v['cik_str']).zfill(10)
                     for v in cik_data.values()}

    rows = []
    log(f'  Querying EDGAR submissions for {len(tickers)} tickers...')
    for i, ticker in enumerate(tickers):
        cik = ticker_to_cik.get(ticker)
        sic = None
        if cik:
            try:
                url = f'https://data.sec.gov/submissions/CIK{cik}.json'
                sub = requests.get(url, headers=headers, timeout=10).json()
                sic = sub.get('sic')
            except Exception:
                pass
        rows.append({'ticker': ticker, 'cik': cik, 'sic': sic,
                     'retrieval_date': retrieval_date})
        if (i + 1) % 100 == 0:
            log(f'    {i+1}/{len(tickers)} completed')
        time.sleep(0.07)  # be polite to EDGAR

    df = pd.DataFrame(rows)
    df.to_csv(EDGAR_CACHE, index=False)
    log(f'  EDGAR SIC retrieval complete. {df["sic"].notna().sum()}/{len(df)} tickers '
        f'have SIC codes. Retrieval date: {retrieval_date}')
    return df


# ===========================================================================
# Section 3: SIC → FF49 mapping
# ===========================================================================

def map_sic_to_ff49(sic_df: pd.DataFrame, ff49: pd.DataFrame) -> pd.DataFrame:
    results = []
    for _, row in sic_df.iterrows():
        if pd.isna(row['sic']):
            ind_num, ind_name = 49, 'Other'
        else:
            try:
                sic_int = int(str(row['sic']).replace('.0', ''))
                mask = (ff49['sic_lo'] <= sic_int) & (sic_int <= ff49['sic_hi'])
                matches = ff49[mask]
                if matches.empty:
                    ind_num, ind_name = 49, 'Other'
                else:
                    ind_num  = int(matches.iloc[0]['industry_num'])
                    ind_name = matches.iloc[0]['industry_name']
            except (ValueError, TypeError):
                ind_num, ind_name = 49, 'Other'
        results.append({'ticker': row['ticker'], 'sic': row.get('sic'),
                        'industry_num': ind_num, 'industry_name': ind_name})
    return pd.DataFrame(results).set_index('ticker')


# ===========================================================================
# Section 4: Price data
# ===========================================================================

def fetch_prices(tickers: list[str]) -> pd.DataFrame:
    import yfinance as yf

    if PRICES_CACHE.exists():
        log(f'  Daily prices: loading from cache ({PRICES_CACHE.name})')
        prices = pd.read_parquet(PRICES_CACHE)
        log(f'  Loaded: {prices.shape[0]:,} days × {prices.shape[1]:,} tickers')
        return prices

    log(f'  Fetching daily adjusted prices for {len(tickers)} tickers '
        f'({STUDY_START_EXTENDED} → {STUDY_END})...')
    prices = yf.download(
        tickers, start=STUDY_START_EXTENDED, end=STUDY_END,
        auto_adjust=True, progress=True
    )['Close']
    prices.to_parquet(PRICES_CACHE)
    log(f'  Prices cached: {prices.shape}')
    return prices


# ===========================================================================
# Section 5: Shares outstanding (for VW weights)
# ===========================================================================

def fetch_shares(available: list[str]) -> pd.Series:
    import yfinance as yf

    if SHARES_CACHE.exists():
        log(f'  Shares outstanding: loading from cache ({SHARES_CACHE.name})')
        sr = pd.read_csv(SHARES_CACHE, index_col=0).squeeze()
        return sr.reindex(available).fillna(sr.median())

    log(f'  Fetching shares outstanding for {len(available)} tickers...')
    shares_dict = {}
    for i, ticker in enumerate(available):
        try:
            fi = yf.Ticker(ticker).fast_info
            shares_dict[ticker] = (
                getattr(fi, 'shares', None)
                or getattr(fi, 'shares_outstanding', None)
            )
        except Exception:
            shares_dict[ticker] = None
        if (i + 1) % 50 == 0:
            log(f'    {i+1}/{len(available)}')
        time.sleep(0.05)

    sr = pd.Series(shares_dict, name='shares_outstanding')
    sr.to_csv(SHARES_CACHE)
    log(f'  Shares fetched: {sr.notna().sum()}/{len(sr)} non-null')
    return sr.reindex(available).fillna(sr.median())


# ===========================================================================
# Section 6: Weight construction
# ===========================================================================

def compute_month_weights(
    approx_mktcap: pd.DataFrame,
    year: int,
    month: int,
) -> pd.Series:
    """Prior-month-end VW weights. Uses last market-cap observation of prior month."""
    bom = pd.Timestamp(year=year, month=month, day=1)
    prior_data = approx_mktcap[approx_mktcap.index < bom]
    if prior_data.empty:
        # Fallback: first available observation in the target month
        cur = approx_mktcap[
            (approx_mktcap.index.year == year) & (approx_mktcap.index.month == month)
        ]
        last_mktcap = cur.iloc[0] if not cur.empty else approx_mktcap.iloc[0]
    else:
        # Last calendar day of prior month's price data
        last_prior_month = (
            prior_data.index.to_series()
            .where(prior_data.index.month == (bom - pd.DateOffset(months=1)).month)
            .dropna()
        )
        if last_prior_month.empty:
            last_mktcap = prior_data.iloc[-1]
        else:
            last_mktcap = prior_data.loc[last_prior_month.iloc[-1]]

    total = last_mktcap.sum()
    if total == 0:
        return pd.Series(0.0, index=last_mktcap.index)
    return last_mktcap / total


# ===========================================================================
# Section 7: CLMX decomposition (single month)
# ===========================================================================

def decompose_month_clmx(
    daily_returns: pd.DataFrame,
    approx_mktcap: pd.DataFrame,
    ticker_industry: pd.DataFrame,
    year: int,
    month: int,
    missing_treatment: str = 'complete_month',
    min_valid_days: int = MIN_VALID_DAYS,
) -> Optional[dict]:
    """
    CLMX three-component decomposition for one calendar month.

    missing_treatment:
        'complete_month' (Option B): include only stocks with no NaN any day.
        'valid_days'    (Option A): include stocks with >= min_valid_days valid returns.

    Returns dict with keys: year, month, MKT, IND, FIRM, n_stocks, n_industries,
    n_trading_days.  Returns None if insufficient data.

    Implementation note (Option A / valid_days):
        Under Option A, stocks present in the valid set may still have NaN on
        some trading days within the month.  The daily VW market return mu_d is
        computed as R.mul(W, axis=1).sum(axis=1) with pandas' default
        skipna=True.

        This is algebraically equivalent to treating each missing stock's return
        as zero on its NaN days, while keeping all original weights unchanged.
        The effective weight sum on a day with k missing stocks equals
        (1 - sum of missing stocks' weights), which is less than 1.  The result
        is NOT equivalent to explicit renormalization (which would rescale the
        remaining weights to sum to 1 and produce a higher mu_d whenever the
        market return is positive).

        Consequence: mu_d under Option A is pulled toward zero relative to
        explicit renormalization on missing-data days.  Whether this biases MKT
        up or down depends on the sign of the market return on those days; the
        effect is asymmetric and month-specific.  This is the structural
        definition of Option A, not a bug.
    """
    mask = (daily_returns.index.year == year) & (daily_returns.index.month == month)
    R_all = daily_returns[mask]
    n_trading_days = len(R_all)
    if n_trading_days < min_valid_days:
        return None

    if missing_treatment == 'complete_month':
        valid = R_all.columns[R_all.notna().all()]
    else:
        valid = R_all.columns[R_all.notna().sum() >= min_valid_days]

    R = R_all[valid]
    if R.empty:
        return None

    W = compute_month_weights(approx_mktcap, year, month)
    W = W.reindex(valid).fillna(0)
    total_w = W.sum()
    if total_w == 0:
        return None
    W = W / total_w

    # Daily VW market return: mu_d
    # Under Option B: no NaNs, so this is exact.
    # Under Option A: NaN tickers are treated as zero-return on missing days (see docstring).
    mu_d = R.mul(W, axis=1).sum(axis=1)
    MKT  = float((mu_d ** 2).sum())
    IND  = 0.0
    FIRM = 0.0
    industries_seen = set()

    for ind_num in ticker_industry.loc[valid, 'industry_num'].unique():
        members = [
            t for t in ticker_industry[ticker_industry['industry_num'] == ind_num].index
            if t in R.columns
        ]
        if not members:
            continue
        W_j = float(W[members].sum())
        if W_j == 0:
            continue
        w_ij = W[members] / W_j
        r_j  = R[members].mul(w_ij, axis=1).sum(axis=1)
        eta  = r_j - mu_d
        IND  += W_j * float((eta ** 2).sum())
        for ticker in members:
            eps   = R[ticker] - r_j
            FIRM += W_j * float(w_ij[ticker]) * float((eps ** 2).sum())
        industries_seen.add(ind_num)

    return {
        'year': year, 'month': month,
        'MKT': MKT, 'IND': IND, 'FIRM': FIRM,
        'n_stocks': int(len(valid)),
        'n_industries': int(len(industries_seen)),
        'n_trading_days': int(n_trading_days),
    }


# ===========================================================================
# Section 8: Full-period decomposition runner
# ===========================================================================

def run_full_period(
    daily_returns: pd.DataFrame,
    approx_mktcap: pd.DataFrame,
    ticker_industry: pd.DataFrame,
    cache_path: Path,
    missing_treatment: str,
    study_start: str = STUDY_START_PRIMARY,
) -> pd.DataFrame:
    if cache_path.exists():
        log(f'  Loading from cache: {cache_path.name}')
        df = pd.read_csv(cache_path)
    else:
        months = pd.date_range(start=study_start, end=STUDY_END, freq='MS')
        log(f'  Running decomposition ({missing_treatment!r}, {len(months)} months)...')
        records = []
        for dt in months:
            r = decompose_month_clmx(
                daily_returns, approx_mktcap, ticker_industry,
                year=dt.year, month=dt.month,
                missing_treatment=missing_treatment,
            )
            if r is not None:
                records.append(r)
            if dt.month == 1:
                log(f'    Completed {dt.year}')
        df = pd.DataFrame(records)
        df.to_csv(cache_path, index=False)
        log(f'  Saved {len(df)} months to {cache_path.name}')

    df['date'] = pd.to_datetime(df[['year', 'month']].assign(day=1))
    df = df.set_index('date').sort_index()
    return df


# ===========================================================================
# Diagnostic helpers
# ===========================================================================

def annual_summary(monthly: pd.DataFrame) -> pd.DataFrame:
    annual = monthly[['MKT', 'IND', 'FIRM']].resample('YE').sum()
    annual.index = annual.index.year
    annual['total']      = annual.sum(axis=1)
    annual['MKT_share']  = annual['MKT']  / annual['total']
    annual['IND_share']  = annual['IND']  / annual['total']
    annual['FIRM_share'] = annual['FIRM'] / annual['total']
    return annual


def subperiod_summary(monthly: pd.DataFrame) -> pd.DataFrame:
    periods = {
        '2010–2014': ('2010-01', '2014-12'),
        '2015–2019': ('2015-01', '2019-12'),
        '2020–2021': ('2020-01', '2021-12'),
        '2022–2024': ('2022-01', '2024-12'),
        '2010–2024': (STUDY_START_PRIMARY[:7], STUDY_END[:7]),
    }
    rows = []
    for lbl, (s, e) in periods.items():
        sub = monthly.loc[s:e, ['MKT', 'IND', 'FIRM']]
        if sub.empty:
            continue
        avg_ann  = sub.mean() * 12
        avg_vol  = np.sqrt(avg_ann) * 100
        total    = avg_ann.sum()
        rows.append({
            'Period':      lbl,
            'MKT_vol%':   f'{avg_vol["MKT"]:.1f}',
            'IND_vol%':   f'{avg_vol["IND"]:.1f}',
            'FIRM_vol%':  f'{avg_vol["FIRM"]:.1f}',
            'FIRM_share': f'{avg_ann["FIRM"]/total:.1%}',
            'N_months':   len(sub),
        })
    return pd.DataFrame(rows)


# ===========================================================================
# Main diagnostic execution
# ===========================================================================

def main() -> None:
    import requests

    section('WP-05 LIVE DATA DIAGNOSTIC PASS')
    log(f'  Run date        : {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}')
    log(f'  Study window    : {STUDY_START_PRIMARY} → {STUDY_END} (primary, D-020)')
    log(f'  Extended window : {STUDY_START_EXTENDED} → {STUDY_END} (D-020 diagnostic)')
    log(f'  Data dir        : {DATA_DIR}')
    log()
    log('  WP-05 output = CLMX replication validation.')
    log('  These results are NOT entered as Parallax H1 evidence.')

    # ─── S0: FF49 crosswalk ───────────────────────────────────────────────────
    section('S0  FF49 SIC Crosswalk')
    ff49 = fetch_ff49_crosswalk()
    log(f'  SIC ranges loaded: {len(ff49)}')
    log(f'  Industry count   : {ff49["industry_num"].nunique()} (expect 49)')
    log(f'  Coverage          : SIC 0001 → 9999')
    ff49_industries = ff49.groupby('industry_num')['industry_name'].first()
    log(f'  First/last industry: {ff49_industries.iloc[0]} / {ff49_industries.iloc[-1]}')

    # ─── S1: Tickers + EDGAR SIC ─────────────────────────────────────────────
    section('S1  S&P 500 Tickers + EDGAR SIC Codes')
    sp500_tickers = fetch_sp500_tickers()
    sic_df = fetch_edgar_sic(sp500_tickers)

    retrieval_date = (sic_df['retrieval_date'].iloc[0]
                      if 'retrieval_date' in sic_df.columns
                      else 'unknown')
    n_total = len(sic_df)
    n_sic_ok = sic_df['sic'].notna().sum()
    log(f'  Total tickers      : {n_total}')
    log(f'  SIC code present   : {n_sic_ok} ({n_sic_ok/n_total:.1%})')
    log(f'  Missing SIC        : {n_total - n_sic_ok} ({(n_total-n_sic_ok)/n_total:.1%})')
    log(f'  EDGAR retrieval    : {retrieval_date}')

    # ─── S2: FF49 mapping ────────────────────────────────────────────────────
    section('S2  SIC → FF49 Industry Mapping')
    ticker_industry = map_sic_to_ff49(sic_df, ff49)
    n_other = (ticker_industry['industry_num'] == 49).sum()
    n_placed = n_total - n_other
    log(f'  Successfully placed  : {n_placed} ({n_placed/n_total:.1%})')
    log(f'  Fallback to "Other"  : {n_other} ({n_other/n_total:.1%})')
    hr()
    log('  Industry distribution (top 15 by count):')
    ind_counts = (ticker_industry.groupby(['industry_num', 'industry_name'])
                  .size().sort_values(ascending=False))
    for (ind_num, ind_name), cnt in ind_counts.head(15).items():
        log(f'    {ind_num:2d} {ind_name:20s}: {cnt:3d}')

    # ─── S3: Price data ───────────────────────────────────────────────────────
    section('S3  Daily Price Data')
    prices = fetch_prices(sp500_tickers)

    classified = list(ticker_industry.index)
    available  = [t for t in classified if t in prices.columns]
    daily_returns = prices[available].pct_change().iloc[1:]
    # Restrict to primary window for main analysis
    dr_primary = daily_returns.loc[STUDY_START_PRIMARY:STUDY_END]
    dr_extended = daily_returns.loc[STUDY_START_EXTENDED:STUDY_END]

    log(f'  Price matrix       : {prices.shape[0]:,} days × {prices.shape[1]:,} tickers')
    log(f'  Tickers classified : {len(available)} / {len(classified)}')
    log(f'  Return matrix (primary 2010-2024):')
    log(f'    Shape            : {dr_primary.shape[0]:,} days × {dr_primary.shape[1]:,} tickers')
    log(f'    Date range       : {dr_primary.index[0].date()} → {dr_primary.index[-1].date()}')
    log(f'    Missing cells    : {dr_primary.isna().sum().sum():,} '
        f'({dr_primary.isna().mean().mean():.2%})')

    # Missing by year
    hr()
    log('  Missing rate by year (primary window):')
    missing_by_year = dr_primary.isna().groupby(dr_primary.index.year).mean().mean(axis=1)
    for yr, rate in missing_by_year.items():
        bar = '█' * int(rate * 200)
        log(f'    {yr}: {rate:.2%}  {bar}')

    # High-missing tickers
    ticker_missing = dr_primary.isna().mean().sort_values(ascending=False)
    n_high_missing = (ticker_missing > 0.10).sum()
    log()
    log(f'  Tickers with > 10% missing: {n_high_missing}')
    if n_high_missing > 0:
        log('  Top 10 by missing rate:')
        for tkr, rate in ticker_missing.head(10).items():
            log(f'    {tkr:8s}: {rate:.1%}')

    # Anomaly screen
    hr()
    extremes = dr_primary.stack().dropna()
    extremes = extremes[extremes.abs() > ANOMALY_THRESHOLD]
    log(f'  Single-day moves > {ANOMALY_THRESHOLD:.0%}: {len(extremes)} observations')
    if len(extremes) > 0:
        ext_df = extremes.reset_index()
        ext_df.columns = ['date', 'ticker', 'return']
        ext_df = ext_df.reindex(ext_df['return'].abs().sort_values(ascending=False).index)
        log('  Top 10 anomalous observations (review individually):')
        for _, row in ext_df.head(10).iterrows():
            log(f'    {row["date"].date()}  {row["ticker"]:8s}  {row["return"]:+.1%}')

    # ─── S4: Coverage diagnostic (D-020 gate) ────────────────────────────────
    section('S4  Coverage Diagnostic (D-020)')
    log('  Coverage = retrieval rate; representativeness assessed separately.')
    log()
    for label, start_yr in [('2010', 2010), ('2007', 2007), ('2005', 2005)]:
        sub = dr_extended.loc[f'{start_yr}':]
        if sub.empty:
            log(f'  Start {label}: no data available')
            continue
        avail_ticker_yr = sub.notna().any(axis=0).sum()
        avg_daily_cov = sub.notna().sum(axis=1).mean()
        # Tickers with history starting after start_yr (partial history)
        first_valid = sub.apply(lambda col: col.first_valid_index())
        partial = (first_valid > pd.Timestamp(year=start_yr, month=3, day=1)).sum()
        log(f'  Start {label}:')
        log(f'    Tickers with any data        : {avail_ticker_yr}')
        log(f'    Avg tickers per day          : {avg_daily_cov:.0f}')
        log(f'    Partial histories (start >Q1): {partial}')
    log()
    log('  SURVIVORSHIP CONTEXT (does not change with coverage):')
    log('  The retrieved universe = current S&P 500 members projected backward.')
    log('  Companies removed from the index for poor performance, delisting,')
    log('  or acquisition are absent from this dataset regardless of coverage rate.')
    log('  High coverage rate does not imply historical representativeness.')
    log('  Bias direction: FIRM variance systematically understated in earlier years.')

    # ─── S5: Weight construction ──────────────────────────────────────────────
    section('S5  VW Weight Audit')
    shares = fetch_shares(available)
    n_fallback = shares.isna().sum() if hasattr(shares, 'isna') else 0
    log(f'  Shares outstanding retrieved : {shares.notna().sum()} / {len(shares)}')
    log(f'  Median fallback applied to   : {n_fallback} tickers')
    log()

    approx_mktcap = prices[available].mul(shares, axis=1)

    # Spot-check representative months
    check_months = [(2010, 1), (2015, 6), (2020, 3), (2022, 1), (2024, 6)]
    log('  Weight spot-checks — prior-month-end VW weights:')
    log(f'    {"Month":<12}  {"Sum":>8}  {"Top ticker":>12}  {"Top wt":>8}')
    hr()
    for yr, mo in check_months:
        try:
            W = compute_month_weights(approx_mktcap, yr, mo)
            W = W.reindex(available).fillna(0)
            W = W / W.sum()
            log(f'    {yr}-{mo:02d}        '
                f'{W.sum():>8.6f}  '
                f'{W.idxmax():>12s}  '
                f'{W.max():>8.3%}')
        except Exception as e:
            log(f'    {yr}-{mo:02d}: ERROR — {e}')

    # Look-ahead check
    log()
    log('  Look-ahead note: weights use prior-month-end market cap.')
    log('  No current-month price data is used to form weights.')

    # ─── S6: Manual CLMX specimen ─────────────────────────────────────────────
    section('S6  Manual CLMX Specimen — March 2020 (COVID month)')
    log('  March 2020 selected: high-volatility month, should produce elevated MKT.')
    log('  Demonstrates full decomposition: daily return → squared components → sum.')
    log()

    EX_YEAR, EX_MONTH = 2020, 3
    mask_ex = ((dr_primary.index.year == EX_YEAR)
               & (dr_primary.index.month == EX_MONTH))
    R_ex_all = dr_primary[mask_ex]
    valid_ex  = R_ex_all.columns[R_ex_all.notna().all()]
    R_ex = R_ex_all[valid_ex]
    W_ex = compute_month_weights(approx_mktcap, EX_YEAR, EX_MONTH)
    W_ex = W_ex.reindex(valid_ex).fillna(0)
    W_ex = W_ex / W_ex.sum()

    mu_ex = R_ex.mul(W_ex, axis=1).sum(axis=1)

    log(f'  March 2020: {len(R_ex)} trading days, {len(valid_ex)} complete-history stocks')
    log()
    log('  Daily VW market return (mu_d):')
    for dt, val in mu_ex.items():
        log(f'    {dt.strftime("%Y-%m-%d")}  {val:+.4f}')
    log()

    MKT_ex = float((mu_ex ** 2).sum())
    log(f'  MKT = Σ mu_d² = {MKT_ex:.8f}')
    log(f'  Annualized MKT vol (×12): {np.sqrt(MKT_ex * 12):.2%}')

    # IND component
    IND_ex = 0.0
    ind_detail_ex = {}
    for ind_num in ticker_industry.loc[valid_ex, 'industry_num'].unique():
        members = [
            t for t in ticker_industry[ticker_industry['industry_num'] == ind_num].index
            if t in R_ex.columns
        ]
        if not members:
            continue
        W_j = float(W_ex[members].sum())
        if W_j == 0:
            continue
        w_ij = W_ex[members] / W_j
        r_j  = R_ex[members].mul(w_ij, axis=1).sum(axis=1)
        eta  = r_j - mu_ex
        contrib = W_j * float((eta ** 2).sum())
        IND_ex += contrib
        ind_name = ticker_industry.loc[members[0], 'industry_name']
        ind_detail_ex[ind_num] = {
            'name': ind_name, 'n': len(members),
            'W_j': W_j, 'contrib': contrib, 'r_j': r_j,
        }

    log()
    log(f'  IND = Σ_j W_j · Σ_d η² = {IND_ex:.8f}')

    # FIRM component
    FIRM_ex = 0.0
    for ind_num, d in ind_detail_ex.items():
        members = [
            t for t in ticker_industry[ticker_industry['industry_num'] == ind_num].index
            if t in R_ex.columns
        ]
        W_j  = float(W_ex[members].sum())
        w_ij = W_ex[members] / W_j
        for ticker in members:
            eps = R_ex[ticker] - d['r_j']
            FIRM_ex += W_j * float(w_ij[ticker]) * float((eps ** 2).sum())

    total_ex = MKT_ex + IND_ex + FIRM_ex
    log(f'  FIRM = Σ_j W_j · Σ_i w_ij · Σ_d ε² = {FIRM_ex:.8f}')
    log()
    log('  ─── Reconciliation ───────────────────────────────────────────────')
    log(f'  MKT   : {MKT_ex:.8f}  ({MKT_ex/total_ex:.1%})')
    log(f'  IND   : {IND_ex:.8f}  ({IND_ex/total_ex:.1%})')
    log(f'  FIRM  : {FIRM_ex:.8f}  ({FIRM_ex/total_ex:.1%})')
    log(f'  Sum   : {total_ex:.8f}')
    vw_total_ex = float((R_ex ** 2).sum().mul(W_ex).sum())
    log(f'  VW-avg individual variance : {vw_total_ex:.8f}')
    log(f'  Gap (cross-product terms)  : {vw_total_ex - total_ex:.2e}')
    log(f'  Gap % of total             : {abs(vw_total_ex - total_ex)/total_ex:.3%}')
    log()
    log('  Reconciliation note: gap = cross-product terms (expected; not a bug).')
    log('  Crisis interpretation: high MKT share expected in March 2020.')

    # ─── S7: Full-period run ──────────────────────────────────────────────────
    section('S7  Full-Period WP-05 Run (both D-018 options)')
    monthly_B = run_full_period(
        dr_primary, approx_mktcap, ticker_industry,
        RESULTS_B_CACHE, 'complete_month',
    )
    monthly_A = run_full_period(
        dr_primary, approx_mktcap, ticker_industry,
        RESULTS_A_CACHE, 'valid_days',
    )

    # Non-negativity check
    for df, label in [(monthly_B, 'Option B'), (monthly_A, 'Option A')]:
        for col in ['MKT', 'IND', 'FIRM']:
            n_neg = (df[col] < 0).sum()
            status = '✓' if n_neg == 0 else f'✗ ({n_neg} NEGATIVE — ERROR)'
            log(f'  {label} {col} non-negativity: {status}')

    # Annual summary — Option B
    log()
    log('  Annual variance shares (Option B / complete_month):')
    ann = annual_summary(monthly_B)
    log(f'  {"Year":>6}  {"MKT%":>8}  {"IND%":>8}  {"FIRM%":>8}  {"N":>4}')
    hr()
    for yr, row in ann.iterrows():
        n = monthly_B[monthly_B.index.year == yr]['n_stocks'].mean()
        log(f'  {yr:>6}  {row["MKT_share"]:>8.1%}  {row["IND_share"]:>8.1%}  '
            f'{row["FIRM_share"]:>8.1%}  {n:>4.0f}')

    # Sub-period summary
    log()
    log('  Sub-period summary (annualized vol, Option B):')
    sp = subperiod_summary(monthly_B)
    log(f'  {"Period":<14}  {"MKT%":>7}  {"IND%":>7}  {"FIRM%":>7}  {"FIRM_sh":>8}  {"N":>4}')
    hr()
    for _, row in sp.iterrows():
        log(f'  {row["Period"]:<14}  {row["MKT_vol%"]:>7}  {row["IND_vol%"]:>7}  '
            f'{row["FIRM_vol%"]:>7}  {row["FIRM_share"]:>8}  {row["N_months"]:>4}')

    # Top/bottom FIRM months
    log()
    log('  Top 5 months by FIRM variance (Option B):')
    top_firm = monthly_B['FIRM'].nlargest(5)
    for dt, val in top_firm.items():
        row = monthly_B.loc[dt]
        log(f'    {dt.strftime("%Y-%m")}  FIRM={val:.6f}  FIRM_share='
            f'{val/(row["MKT"]+row["IND"]+row["FIRM"]):.1%}  n={row["n_stocks"]:.0f}')

    log()
    log('  Bottom 5 months by FIRM variance (Option B):')
    bot_firm = monthly_B['FIRM'].nsmallest(5)
    for dt, val in bot_firm.items():
        row = monthly_B.loc[dt]
        log(f'    {dt.strftime("%Y-%m")}  FIRM={val:.6f}  FIRM_share='
            f'{val/(row["MKT"]+row["IND"]+row["FIRM"]):.1%}  n={row["n_stocks"]:.0f}')

    # ─── S8: D-018 evidence ───────────────────────────────────────────────────
    section('S8  D-018 Evidence: Option A vs Option B')
    log('  Comparison basis: MKT, IND, FIRM, component shares, n_stocks.')
    log('  Adjudication requires methodological defensibility + empirical sensitivity.')
    log()

    # Align on shared index
    shared = monthly_A.index.intersection(monthly_B.index)
    mA = monthly_A.loc[shared]
    mB = monthly_B.loc[shared]
    log(f'  Months compared: {len(shared)} (A: {len(monthly_A)}, B: {len(monthly_B)})')
    log()

    # Universe size
    mean_n_A = mA['n_stocks'].mean()
    mean_n_B = mB['n_stocks'].mean()
    log(f'  Universe size:')
    log(f'    Option A (valid_days)      : {mean_n_A:.0f} stocks/month avg')
    log(f'    Option B (complete_month)  : {mean_n_B:.0f} stocks/month avg')
    log(f'    Avg difference             : {mean_n_A - mean_n_B:+.0f} stocks/month')

    # Component-level relative differences
    log()
    log('  Median absolute relative difference per component:')
    for comp in ['MKT', 'IND', 'FIRM']:
        diff = (mA[comp] - mB[comp]).abs()
        rel  = (diff / mB[comp].replace(0, np.nan)).dropna()
        log(f'    {comp:4s}: median={rel.median():.2%}  max={rel.max():.2%}  '
            f'p90={rel.quantile(0.90):.2%}')

    # Component share comparison
    log()
    log('  Average component shares by option:')
    for label, df in [('Option A', mA), ('Option B', mB)]:
        tot = df['MKT'] + df['IND'] + df['FIRM']
        log(f'    {label}: MKT={df["MKT"].sum()/tot.sum():.1%}  '
            f'IND={df["IND"].sum()/tot.sum():.1%}  '
            f'FIRM={df["FIRM"].sum()/tot.sum():.1%}')

    # Stress periods
    log()
    log('  D-018 comparison in stress periods:')
    stress_periods = {
        'COVID (2020-03)': '2020-03',
        'COVID (2020-04)': '2020-04',
        'Rate hike (2022-06)': '2022-06',
    }
    for label, mo in stress_periods.items():
        if mo in mA.index.strftime('%Y-%m') and mo in mB.index.strftime('%Y-%m'):
            rA = mA[mA.index.strftime('%Y-%m') == mo]
            rB = mB[mB.index.strftime('%Y-%m') == mo]
            if not rA.empty and not rB.empty:
                for comp in ['MKT', 'IND', 'FIRM']:
                    vA, vB = float(rA[comp].iloc[0]), float(rB[comp].iloc[0])
                    reldiff = abs(vA - vB) / vB if vB != 0 else float('nan')
                    log(f'    {label} {comp}: A={vA:.6f}  B={vB:.6f}  '
                        f'rel_diff={reldiff:.2%}')

    # Option A structural note
    log()
    log('  STRUCTURAL NOTE (Option A):')
    log('  R.mul(W, axis=1).sum(axis=1) with skipna=True is algebraically')
    log('  equivalent to treating each missing stock as returning 0.0 on its NaN')
    log('  days, while leaving all other weights at their original values.')
    log('  This is NOT renormalization: under renormalization, the remaining')
    log('  weights are rescaled to sum to 1 and mu_d is higher (when the market')
    log('  is positive) than what skipna produces. Under skipna, the effective')
    log('  weight sum on a missing-data day equals 1 minus the sum of the missing')
    log('  stocks\' original weights — less than 1. mu_d is pulled toward zero.')
    log('  Whether this inflates or deflates MKT in any given month depends on')
    log('  the sign of mu_d on the missing-data days; the direction is not fixed.')

    # ─── S9: D-020 evidence ───────────────────────────────────────────────────
    section('S9  D-020 Evidence: 2005–2009 Extension Assessment')
    log('  Evaluating separately: coverage (retrieval) vs representativeness.')
    log()
    log('  COVERAGE DIAGNOSTIC (what the data can provide):')

    # Coverage by year 2005-2009
    for yr in range(2005, 2010):
        yr_data = dr_extended.loc[str(yr)]
        if yr_data.empty:
            log(f'    {yr}: no data')
            continue
        n_tickers_with_data = yr_data.notna().any(axis=0).sum()
        daily_avg = yr_data.notna().sum(axis=1).mean()
        pct_coverage = daily_avg / len(available)
        # Late-starters (first observation after Jan of that year)
        first_obs = yr_data.apply(lambda c: c.first_valid_index())
        late_starters = (first_obs > pd.Timestamp(year=yr, month=3, day=1)).sum()
        log(f'    {yr}: tickers_any_data={n_tickers_with_data:3d}  '
            f'avg_daily={daily_avg:.0f} ({pct_coverage:.1%})  '
            f'late_starters={late_starters}')

    log()
    log('  REPRESENTATIVENESS ASSESSMENT (structural, not data-dependent):')
    log()
    log('  The current-constituent S&P 500 universe includes only companies that')
    log('  survived to 2025. For 2005–2009, this creates a survivorship-biased')
    log('  backward sample — companies that were in the index in 2005–2009 but')
    log('  were removed (Bear Stearns, Lehman Brothers, Washington Mutual, Wachovia')
    log('  and many others removed around the GFC) are absent entirely.')
    log()
    log('  This is not a coverage problem — it is a structural problem. A dataset')
    log('  with 85% ticker coverage where the missing 15% are the companies that')
    log('  failed during the GFC is not 85% representative; it is systematically')
    log('  biased in a direction that understates historical FIRM variance during')
    log('  the most historically interesting period.')
    log()
    log('  The 2005–2009 question therefore has two distinct answers:')
    log('  Coverage   : potentially acceptable retrieval rates (data exists)')
    log('  Representativeness: materially survivorship-biased for the GFC period')
    log()
    log('  Decision required from Matt: does the 2005–2009 replication serve the')
    log('  research goal despite the known survivorship concentration, or does it')
    log('  risk producing a misleading baseline? This is a methodological judgment,')
    log('  not a coverage threshold question.')

    # ─── Generate charts ──────────────────────────────────────────────────────
    section('Generating Charts')

    # Chart 1: Full-period component time series (Option B)
    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
    fig.suptitle('CLMX Variance Decomposition — S&P 500 (WP-05 Replication)\n'
                 'NOT Parallax H1 evidence — replication validation only',
                 fontsize=11, fontweight='bold')
    colors = {'MKT': '#2166ac', 'IND': '#4dac26', 'FIRM': '#d01c8b'}
    for ax, comp in zip(axes, ['MKT', 'IND', 'FIRM']):
        roll = np.sqrt(monthly_B[comp].rolling(12).sum()) * 100
        ax.plot(roll.index, roll, color=colors[comp], linewidth=1.5)
        ax.fill_between(roll.index, roll, alpha=0.15, color=colors[comp])
        ax.set_ylabel(f'{comp}\nAnn. Vol (%)', fontsize=9)
        ax.grid(alpha=0.3, linestyle='--')
        for evt_dt, lbl in [('2020-03', 'COVID'), ('2022-01', 'Rate hikes')]:
            ax.axvline(pd.Timestamp(evt_dt), color='gray', linestyle=':', alpha=0.7)
    axes[-1].set_xlabel('Date')
    plt.tight_layout()
    out1 = DATA_DIR / 'wp05_fig01_components.png'
    plt.savefig(out1, dpi=150, bbox_inches='tight')
    plt.close()
    log(f'  Chart 1 saved: {out1}')

    # Chart 2: Variance shares (Option B)
    fig, ax = plt.subplots(figsize=(12, 5))
    roll_tot = monthly_B[['MKT', 'IND', 'FIRM']].rolling(24).sum()
    roll_sh  = roll_tot.div(roll_tot.sum(axis=1), axis=0)
    ax.stackplot(roll_sh.index,
                 roll_sh['FIRM'] * 100, roll_sh['IND'] * 100, roll_sh['MKT'] * 100,
                 labels=['FIRM', 'IND', 'MKT'],
                 colors=['#d01c8b', '#4dac26', '#2166ac'], alpha=0.8)
    ax.set_ylabel('Variance Share (%)')
    ax.set_title('Variance Shares: 24-Month Rolling | WP-05 Replication — NOT H1 evidence')
    ax.legend(loc='upper left', fontsize=10)
    ax.set_ylim(0, 100)
    ax.grid(alpha=0.3, linestyle='--', axis='y')
    out2 = DATA_DIR / 'wp05_fig02_shares.png'
    plt.tight_layout()
    plt.savefig(out2, dpi=150, bbox_inches='tight')
    plt.close()
    log(f'  Chart 2 saved: {out2}')

    # Chart 3: D-018 comparison
    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
    fig.suptitle('D-018: Option A (valid_days) vs Option B (complete_month)\n'
                 'Adjudication: methodological defensibility + all-component sensitivity',
                 fontsize=11, fontweight='bold')
    for ax, comp in zip(axes[:2], ['MKT', 'FIRM']):
        roll_A = np.sqrt(mA[comp].rolling(12).sum()) * 100
        roll_B = np.sqrt(mB[comp].rolling(12).sum()) * 100
        ax.plot(roll_A.index, roll_A, label='Option A (valid_days)',
                color='#d01c8b', linewidth=1.5)
        ax.plot(roll_B.index, roll_B, label='Option B (complete_month)',
                color='#2166ac', linewidth=1.5, linestyle='--')
        ax.set_ylabel(f'{comp} Ann. Vol (%)', fontsize=9)
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3, linestyle='--')
    ax = axes[2]
    ax.plot(mA.index, mA['n_stocks'], label='Option A', color='#d01c8b')
    ax.plot(mB.index, mB['n_stocks'], label='Option B', color='#2166ac', linestyle='--')
    ax.set_ylabel('# Stocks', fontsize=9)
    ax.set_xlabel('Date')
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3, linestyle='--')
    plt.tight_layout()
    out3 = DATA_DIR / 'wp05_fig03_d018.png'
    plt.savefig(out3, dpi=150, bbox_inches='tight')
    plt.close()
    log(f'  Chart 3 saved: {out3}')

    # Chart 4: D-020 coverage 2005-2024
    fig, ax = plt.subplots(figsize=(12, 4))
    daily_cov = dr_extended.notna().sum(axis=1)
    ax.plot(daily_cov.index, daily_cov, linewidth=0.6, color='steelblue', alpha=0.8)
    ax.axvline(pd.Timestamp('2010-01-01'), color='orange', linestyle='--',
               label='D-020 primary start (2010)')
    ax.axvline(pd.Timestamp('2005-01-01'), color='red', linestyle=':',
               label='D-020 extension candidate (2005)')
    ax.set_ylabel('# Tickers with Return Data')
    ax.set_title('Daily Universe Coverage — 2005–2024 (D-020 diagnostic)')
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3, linestyle='--')
    plt.tight_layout()
    out4 = DATA_DIR / 'wp05_fig04_d020_coverage.png'
    plt.savefig(out4, dpi=150, bbox_inches='tight')
    plt.close()
    log(f'  Chart 4 saved: {out4}')

    # ─── Final summary ────────────────────────────────────────────────────────
    section('DECISIONS REQUIRING HUMAN ADJUDICATION')
    log('  The following decisions require human adjudication.')
    log('  Evidence is in sections above; the decision is the researcher\'s.')
    log()
    log('  D-018 (OPEN): Option A (valid_days) vs Option B (complete_month)')
    log('    → Review D-018 section above: component-level sensitivities,')
    log('      Option A structural note (zero-return imputation), universe size gap.')
    log('    → Decision basis: methodological defensibility + empirical sensitivity.')
    log()
    log('  D-020 (OPEN): Keep 2010-2024 or extend to 2005-2024')
    log('    → Review D-020 section above: coverage numbers + representativeness note.')
    log('    → Key question: GFC survivorship concentration makes 2005-2009 a')
    log('      potentially misleading baseline despite usable coverage rates.')
    log('    → This is a research design judgment, not a threshold question.')
    log()
    section('DIAGNOSTIC RECOMMENDATION')
    log('  ONE RECOMMENDATION ONLY (diagnostic output, not an authorized decision):')
    log()
    log('  Recommend resolving D-018 as Option B (complete_month) on methodological')
    log('  grounds — not because the FIRM series difference is small, but because')
    log('  Option B produces a day-consistent VW portfolio within each month.')
    log('  Option A treats missing returns as zero (skipna), which pulls mu_d toward')
    log('  zero on missing-data days and complicates interpretation of the IND and')
    log('  FIRM components. The CLMX estimator assumes a fixed within-month basket')
    log('  conceptually (it sums squared daily components for a given stock set).')
    log('  Option B is more faithful to that conceptual structure.')
    log()
    log('  This recommendation should be reviewed before D-018 is registered as resolved.')
    log()
    log('  On D-020: make no recommendation. The GFC survivorship question is a')
    log('  research design judgment about what the project is trying to measure.')

    save_report()


if __name__ == '__main__':
    main()
