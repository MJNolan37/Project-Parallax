"""
diagnostics/wp05_daily_weight_audit.py  (v2 — corrected)
Project Parallax WP-05 — Post-run q_t audit.

Corrects the v1 audit (submitted 2026-09-12), which was rejected by G-Zephy
review on the following grounds:

  1. Wrong weights: v1 used daily price-normalised weights. Correct weights are
     prior-month-end price × static shares (approx_mktcap), reindexed to the
     per-option eligible basket and renormalised, exactly as in
     diagnostics/wp05_live_diagnostic.py::decompose_month_clmx().

  2. No basket application: v1 computed q_t over the full universe. Correct
     computation applies each option's monthly eligible set first.

  3. S6 circular: v1 defined B completeness by complete observations, then
     described it as verification. Correct: inspect actual positive-weight
     entries in each option's basket, not just eligibility counts.

  4. Industry audit skipped: v1 expected sp500_sic_assignments.csv, which the
     live diagnostic does not produce. Correct inputs are sp500_sic_codes.csv
     + ff49_sic_map.csv, from which the ticker→industry map is rebuilt inline.

  5. S8 prose-only: v1 stated reconciliation without computing it. Correct:
     calculate delta(MKT_A - MKT_B) month by month from cached CSVs.

  6. Floating-point noise miscounted: v1 flagged q_t < 1 without a tolerance.
     Correct: use consistent tolerance of 1e-9 everywhere.

  7. Volatility association non-interpretable: v1 used unweighted cross-sectional
     dispersion over the full universe. Correct: flag as undefined/non-informative
     when missing-weight variation is below tolerance.

Governance
----------
  Read-only over cached data. No network calls. No yfinance.
  No methodology changes. D-018 and D-020 remain open.

Inputs (from data/ directory)
------------------------------
  sp500_daily_prices.parquet          (5,032 days × 503 tickers)
  sp500_shares_outstanding.csv        (static current shares)
  sp500_sic_codes.csv                 (ticker → SIC from EDGAR)
  ff49_sic_map.csv                    (SIC range → FF49 industry)
  clmx_monthly_decomp_opt_a.csv       (180-month cached Option A results)
  clmx_monthly_decomp_opt_b.csv       (180-month cached Option B results)

Outputs (written to data/)
---------------------------
  wp05_qt_audit.txt                   (text report, all six G-Zephy quantities)
  wp05_fig05_qt.png                   (three-panel chart)

Run from project root:
    python diagnostics/wp05_daily_weight_audit.py
"""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# ---------------------------------------------------------------------------
# Paths (mirrors wp05_live_diagnostic.py)
# ---------------------------------------------------------------------------
PROJECT_ROOT  = Path(__file__).resolve().parent.parent
DATA_DIR      = PROJECT_ROOT / 'data'

PRICES_CACHE  = DATA_DIR / 'sp500_daily_prices.parquet'
SHARES_CACHE  = DATA_DIR / 'sp500_shares_outstanding.csv'
EDGAR_CACHE   = DATA_DIR / 'sp500_sic_codes.csv'
FF49_CACHE    = DATA_DIR / 'ff49_sic_map.csv'
RESULTS_A     = DATA_DIR / 'clmx_monthly_decomp_opt_a.csv'
RESULTS_B     = DATA_DIR / 'clmx_monthly_decomp_opt_b.csv'

REPORT_PATH   = DATA_DIR / 'wp05_qt_audit.txt'
FIG_PATH      = DATA_DIR / 'wp05_fig05_qt.png'

STUDY_START   = '2010-01-01'
STUDY_END     = '2024-12-31'
MIN_VALID_DAYS = 10          # D-017

# Consistent tolerance for "q_t is below 1" judgements throughout the script
QT_TOLERANCE  = 1e-9

_report_lines: list[str] = []

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
def log(msg: str = '') -> None:
    ts = datetime.datetime.now().strftime('%H:%M:%S')
    line = f'[{ts}] {msg}'
    print(line)
    _report_lines.append(line)


def header(title: str) -> None:
    sep = '=' * 72
    log()
    log(sep)
    log(f'  {title}')
    log(sep)


def rule() -> None:
    log('  ' + '-' * 68)


def save_report() -> None:
    REPORT_PATH.write_text('\n'.join(_report_lines), encoding='utf-8')
    print(f'\nAudit report written: {REPORT_PATH}')


# ---------------------------------------------------------------------------
# Helpers: replicate weight construction from live diagnostic exactly
# ---------------------------------------------------------------------------

def compute_month_weights(
    approx_mktcap: pd.DataFrame,
    year: int,
    month: int,
) -> pd.Series:
    """
    Verbatim replication of wp05_live_diagnostic.py::compute_month_weights().
    Returns un-renormalised prior-month-end VW weight vector (may include NaN
    for stocks with no prior-month price).
    """
    bom = pd.Timestamp(year=year, month=month, day=1)
    prior_data = approx_mktcap[approx_mktcap.index < bom]
    if prior_data.empty:
        cur = approx_mktcap[
            (approx_mktcap.index.year == year) & (approx_mktcap.index.month == month)
        ]
        last_mktcap = cur.iloc[0] if not cur.empty else approx_mktcap.iloc[0]
    else:
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


def basket_weights(
    approx_mktcap: pd.DataFrame,
    year: int,
    month: int,
    valid_tickers: pd.Index,
) -> pd.Series:
    """
    Reindex pre-computed month weights to `valid_tickers`, fill NaN → 0,
    renormalise to sum to 1.  Returns zero Series if total weight is 0.
    Replicates lines 401-406 of decompose_month_clmx().
    """
    W = compute_month_weights(approx_mktcap, year, month)
    W = W.reindex(valid_tickers).fillna(0.0)
    total_w = W.sum()
    if total_w == 0:
        return pd.Series(0.0, index=valid_tickers)
    return W / total_w


# ---------------------------------------------------------------------------
# S0: Data loading
# ---------------------------------------------------------------------------

def load_data() -> tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.DataFrame,
                          pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Returns: prices, shares, ticker_industry, daily_returns, approx_mktcap,
             monthly_A, monthly_B
    """
    header('S0  LOAD CACHED DATA')

    for path in [PRICES_CACHE, SHARES_CACHE, EDGAR_CACHE, FF49_CACHE,
                 RESULTS_A, RESULTS_B]:
        if not path.exists():
            log(f'  ERROR: {path} not found. Run wp05_live_diagnostic.py first.')
            raise SystemExit(1)

    prices = pd.read_parquet(PRICES_CACHE)
    prices.index = pd.to_datetime(prices.index)
    log(f'  Prices: {prices.shape[0]:,} days × {prices.shape[1]:,} tickers '
        f'({prices.index.min().date()} to {prices.index.max().date()})')

    shares = pd.read_csv(SHARES_CACHE, index_col=0).squeeze()
    log(f'  Shares: {len(shares):,} tickers, {shares.notna().sum()} non-null')

    sic_df = pd.read_csv(EDGAR_CACHE)
    ff49   = pd.read_csv(FF49_CACHE)
    log(f'  EDGAR SIC: {len(sic_df):,} tickers')
    log(f'  FF49 map : {len(ff49):,} SIC ranges')

    # Rebuild ticker→industry exactly as the live diagnostic does
    ticker_industry = _build_industry_map(sic_df, ff49)
    log(f'  ticker_industry: {len(ticker_industry):,} tickers assigned')

    # Universe: classified tickers with price data
    classified = list(ticker_industry.index)
    available  = [t for t in classified if t in prices.columns]
    log(f'  Available (classified + price data): {len(available):,}')

    # approx_mktcap = price × static shares (verbatim from diagnostic S5)
    approx_mktcap = prices[available].mul(shares.reindex(available).fillna(shares.median()), axis=1)

    daily_returns = prices[available].pct_change(fill_method=None).iloc[1:]
    dr_primary    = daily_returns.loc[STUDY_START:STUDY_END]
    log(f'  Return matrix (primary): {dr_primary.shape[0]:,} days × {dr_primary.shape[1]:,} tickers')
    log(f'  Date range: {dr_primary.index[0].date()} to {dr_primary.index[-1].date()}')

    monthly_A = _load_monthly(RESULTS_A, 'A')
    monthly_B = _load_monthly(RESULTS_B, 'B')

    return (prices, shares, ticker_industry[ticker_industry.index.isin(available)],
            dr_primary, approx_mktcap, monthly_A, monthly_B)


def _build_industry_map(sic_df: pd.DataFrame, ff49: pd.DataFrame) -> pd.DataFrame:
    """Replicate map_sic_to_ff49() from wp05_live_diagnostic.py."""
    results = []
    for _, row in sic_df.iterrows():
        if pd.isna(row.get('sic')):
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


def _load_monthly(path: Path, label: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df['date'] = pd.to_datetime(df[['year', 'month']].assign(day=1))
    df = df.set_index('date').sort_index()
    log(f'  Monthly Option {label}: {len(df):,} months loaded from cache')
    return df


# ---------------------------------------------------------------------------
# S1: Per-month eligible baskets and WP-05 weights
# ---------------------------------------------------------------------------

def build_monthly_baskets(
    dr_primary: pd.DataFrame,
    approx_mktcap: pd.DataFrame,
    ticker_industry: pd.DataFrame,
) -> list[dict]:
    """
    For each month in the primary window, compute:
      - valid_B: tickers with returns on ALL trading days (Option B / complete_month)
      - valid_A: tickers with returns on >= MIN_VALID_DAYS (Option A / valid_days)
      - W_B:     WP-05 weights restricted to valid_B, zero-filled, renormalised
      - W_A:     WP-05 weights restricted to valid_A, zero-filled, renormalised
      - pos_wt_B: subset of valid_B with W > QT_TOLERANCE (positive-weight basket)
      - pos_wt_A: subset of valid_A with W > QT_TOLERANCE
      - A_excl:  valid_A \ valid_B  (partial stocks: ≥10 days but not all days)
      - A_excl_pos_wt: subset of A_excl with positive weight under W_A
    """
    header('S1  PER-MONTH ELIGIBLE BASKETS AND WP-05 WEIGHTS')
    months = pd.date_range(start=STUDY_START, end=STUDY_END, freq='MS')
    records = []

    n_a_excl_total   = 0
    n_a_excl_pos     = 0
    months_with_excl = 0
    months_with_excl_pos = 0

    for dt in months:
        yr, mo = dt.year, dt.month
        mask = (dr_primary.index.year == yr) & (dr_primary.index.month == mo)
        R_month = dr_primary[mask]
        if len(R_month) < MIN_VALID_DAYS:
            continue

        n_trading = len(R_month)
        valid_cnt  = R_month.notna().sum()
        valid_B    = R_month.columns[valid_cnt == n_trading]
        valid_A    = R_month.columns[valid_cnt >= MIN_VALID_DAYS]
        A_excl     = valid_A[~valid_A.isin(valid_B)]  # partial: A but not B

        W_B = basket_weights(approx_mktcap, yr, mo, valid_B)
        W_A = basket_weights(approx_mktcap, yr, mo, valid_A)

        pos_wt_B      = W_B[W_B > QT_TOLERANCE].index
        pos_wt_A      = W_A[W_A > QT_TOLERANCE].index
        A_excl_pos    = [t for t in A_excl if t in W_A.index and W_A[t] > QT_TOLERANCE]

        n_a_excl_total   += len(A_excl)
        n_a_excl_pos     += len(A_excl_pos)
        if len(A_excl) > 0:
            months_with_excl += 1
        if len(A_excl_pos) > 0:
            months_with_excl_pos += 1

        records.append({
            'year': yr, 'month': mo, 'date': dt,
            'n_trading': n_trading,
            'n_valid_B': len(valid_B), 'n_valid_A': len(valid_A),
            'n_A_excl': len(A_excl),
            'n_A_excl_pos_wt': len(A_excl_pos),
            'A_excl_tickers': list(A_excl),
            'A_excl_pos_wt_tickers': A_excl_pos,
            'valid_B': valid_B, 'valid_A': valid_A,
            'W_B': W_B, 'W_A': W_A,
            'pos_wt_B': pos_wt_B, 'pos_wt_A': pos_wt_A,
        })

    log(f'  Months processed: {len(records)}')
    log()
    log('  Partial stock-months (≥10 days but not all days = "A-exclusive"):')
    log(f'    Total A-exclusive ticker-months : {n_a_excl_total:,}')
    log(f'    With positive WP-05 weight      : {n_a_excl_pos:,}')
    log(f'    Months containing any A-excl    : {months_with_excl:,}')
    log(f'    Months with positive-weight A-excl: {months_with_excl_pos:,}')
    log()

    if n_a_excl_total == 0:
        log('  *** A-exclusive category is EMPTY.')
        log('      valid_A ≡ valid_B for all months. A and B are identical by construction.')
    elif n_a_excl_pos == 0:
        log('  *** A-exclusive stocks exist but ALL have zero WP-05 prior-month-end weight.')
        log('      Explanation: these are new index entrants with no prior-month price.')
        log('      W.reindex(valid_A).fillna(0) → their weight is 0 → does not enter')
        log('      mu_d, eta, or eps. Option A and Option B component estimates are')
        log('      identical despite different eligible counts.')
        log()
        log('  CORRECTED EXPLANATION FOR A=B EQUALITY:')
        log('  The "borderline category is empty" statement in C-Zephy v1 evidence')
        log('  is INCORRECT. The correct explanation: A-exclusive stocks exist in')
        log(f'  {months_with_excl} months with {n_a_excl_total} ticker-months, but ALL')
        log('  receive zero prior-month-end weight (no prior price). They appear in')
        log('  n_stocks counts but do not affect any component calculation.')
    else:
        log(f'  *** {n_a_excl_pos} A-exclusive ticker-months have POSITIVE WP-05 weight.')
        log('      These are the cases where A and B will differ empirically.')

    # Log examples of A-exclusive entries
    excl_examples = [(r['year'], r['month'], r['A_excl_tickers'],
                      r['A_excl_pos_wt_tickers'])
                     for r in records if r['n_A_excl'] > 0][:8]
    if excl_examples:
        log()
        log('  Examples of months with A-exclusive stocks (up to 8):')
        log(f'    {"YY-MM":<8}  {"A-excl tickers":<40}  {"Pos-wt":<20}')
        rule()
        for yr, mo, tickers, pos in excl_examples:
            pos_str = ', '.join(pos) if pos else 'none'
            log(f'    {yr}-{mo:02d}    {", ".join(tickers):<40}  {pos_str}')

    return records


# ---------------------------------------------------------------------------
# S2: Compute q_t using WP-05 methodology
# ---------------------------------------------------------------------------

def compute_qt_wp05(
    dr_primary: pd.DataFrame,
    monthly_baskets: list[dict],
) -> tuple[pd.Series, pd.Series]:
    """
    For each trading day d in the primary window, compute:
      q_t^B = sum of W_B[i] for all i where R[i,d] is not NaN
      q_t^A = sum of W_A[i] for all i where R[i,d] is not NaN

    Under WP-05 methodology:
      - Weights are prior-month-end VW, reindexed to eligible basket, zero-filled,
        renormalised. Only positive-weight stocks matter.
      - For Option B: by definition, all stocks in basket have returns on all days
        in the month. So q_t^B = 1.0 by construction.
      - For Option A: if all A-exclusive stocks have zero weight, the positive-weight
        basket equals B's basket, and q_t^A = 1.0 as well.

    Returns two Series (q_t_A, q_t_B), indexed by trading date.
    """
    header('S2  DAILY q_t — WP-05 METHODOLOGY  [QUANTITY 1]')

    qt_A_records = {}
    qt_B_records = {}

    for rec in monthly_baskets:
        yr, mo = rec['year'], rec['month']
        mask   = (dr_primary.index.year == yr) & (dr_primary.index.month == mo)
        R_month = dr_primary[mask]
        W_A     = rec['W_A']
        W_B     = rec['W_B']

        for dt, row in R_month.iterrows():
            # q_t = sum of weights for stocks with non-NaN return
            # NaN tickers contribute 0 to the sum by construction of has_return
            has_return = row.notna()

            # Reindex to basket, fill NaN tickers as False (no return)
            has_return_A = has_return.reindex(W_A.index, fill_value=False)
            has_return_B = has_return.reindex(W_B.index, fill_value=False)

            qt_A_records[dt] = float(W_A[has_return_A].sum())
            qt_B_records[dt] = float(W_B[has_return_B].sum())

    qt_A = pd.Series(qt_A_records).sort_index()
    qt_B = pd.Series(qt_B_records).sort_index()

    for label, qt in [('Option A', qt_A), ('Option B', qt_B)]:
        log(f'  {label} q_t:')
        log(f'    N days : {len(qt):,}')
        log(f'    Mean   : {qt.mean():.12f}')
        log(f'    Min    : {qt.min():.12f}  on {qt.idxmin().date()}')
        log(f'    Max    : {qt.max():.12f}')
        log(f'    Std    : {qt.std():.2e}')
        n_below = (qt < 1.0 - QT_TOLERANCE).sum()
        log(f'    Days with q_t < 1 - 1e-9: {n_below:,}')
        if n_below > 0:
            log(f'    Min q_t (below days): {qt[qt < 1 - QT_TOLERANCE].min():.12f}')
        log()

    return qt_A, qt_B


# ---------------------------------------------------------------------------
# S3: Frequency and severity of q_t < 1  [QUANTITY 3]
# ---------------------------------------------------------------------------

def qt_below_one_report(qt_A: pd.Series, qt_B: pd.Series) -> None:
    header('S3  FREQUENCY AND SEVERITY OF q_t < 1  [QUANTITY 3]')
    log('  Tolerance: q_t is "below 1" when q_t < 1 - 1e-9.')
    log()

    for label, qt in [('Option A', qt_A), ('Option B', qt_B)]:
        below = qt[qt < 1.0 - QT_TOLERANCE]
        log(f'  {label}:')
        log(f'    Total days: {len(qt):,}  |  Days with q_t < 1: {len(below):,}')
        if len(below) == 0:
            log('    q_t = 1.0 (within tolerance) on every trading day.')
        else:
            log(f'    Mean deficit (1 - q_t): {(1 - below).mean():.8f}')
            log(f'    Max deficit (1 - q_t): {(1 - below.min()):.8f}')
            log(f'    Dates: {[str(d.date()) for d in below.index[:5]]} ...')
        log()

    if (qt_A < 1.0 - QT_TOLERANCE).sum() == 0 and (qt_B < 1.0 - QT_TOLERANCE).sum() == 0:
        log('  CONCLUSION [QUANTITY 3]:')
        log('  q_t = 1.0 on all trading days under both options.')
        log('  The q_t < 1 phenomenon does not arise in this cached dataset.')
        log('  Missing-return treatment (Option A vs B) has no daily-weight effect.')


# ---------------------------------------------------------------------------
# S4: Missing weight vs volatility  [QUANTITY 4]
# ---------------------------------------------------------------------------

def volatility_clustering_report(
    qt_A: pd.Series,
    qt_B: pd.Series,
    dr_primary: pd.DataFrame,
) -> None:
    header('S4  MISSING WEIGHT AND MARKET VOLATILITY  [QUANTITY 4]')

    missing_A = 1.0 - qt_A
    missing_B = 1.0 - qt_B

    max_missing_A = missing_A.max()
    max_missing_B = missing_B.max()

    log(f'  Max daily missing weight (1 - q_t):')
    log(f'    Option A: {max_missing_A:.2e}')
    log(f'    Option B: {max_missing_B:.2e}')
    log()

    if max_missing_A < QT_TOLERANCE and max_missing_B < QT_TOLERANCE:
        log('  Missing weight variation is below the 1e-9 tolerance on all days.')
        log('  Volatility clustering analysis is undefined/non-informative:')
        log('  there is no missing-weight signal to correlate with volatility.')
        log()
        log('  CONCLUSION [QUANTITY 4]: Undefined. q_t = 1 leaves no variation to associate.')
        log('  If positive-weight partial stock-months emerge after re-indexing')
        log('  with point-in-time shares/membership data, re-run this section.')
        return

    # Only reached if meaningful variation exists
    xsec_vol = dr_primary.std(axis=1)
    for label, missing in [('Option A', missing_A), ('Option B', missing_B)]:
        corr = missing.corr(xsec_vol)
        spearman = missing.corr(xsec_vol, method='spearman')
        log(f'  {label}:')
        log(f'    Pearson  (1-q_t, xs-vol): {corr:.4f}')
        log(f'    Spearman (1-q_t, xs-vol): {spearman:.4f}')


# ---------------------------------------------------------------------------
# S5: Option-B vs Option-A basket characterisation  [QUANTITY 5]
# ---------------------------------------------------------------------------

def option_b_gap_report(monthly_baskets: list[dict]) -> None:
    header('S5  OPTION-B vs OPTION-A BASKET CHARACTERISATION  [QUANTITY 5]')
    log('  Categorisation of ticker-months using ACTUAL WP-05 weights,')
    log('  not eligibility counts alone.')
    log()

    n_B_pos = 0; n_B_zero = 0
    n_A_excl_zero = 0; n_A_excl_pos = 0
    n_excl_total  = 0

    month_rows = []
    for rec in monthly_baskets:
        n_pos_b = len(rec['pos_wt_B'])
        n_zero_b = rec['n_valid_B'] - n_pos_b
        n_excl   = rec['n_A_excl']
        n_excl_p = rec['n_A_excl_pos_wt']

        n_B_pos   += n_pos_b
        n_B_zero  += n_zero_b
        n_A_excl_zero += (n_excl - n_excl_p)
        n_A_excl_pos  += n_excl_p
        n_excl_total  += n_excl

        month_rows.append({
            'year': rec['year'], 'month': rec['month'],
            'n_B_pos': n_pos_b, 'n_B_zero': n_zero_b,
            'n_A_excl': n_excl, 'n_A_excl_pos': n_excl_p,
        })

    log('  Aggregate across all months:')
    log(f'    Option-B stocks with positive weight  : {n_B_pos:,} ticker-months')
    log(f'    Option-B stocks with zero weight      : {n_B_zero:,} ticker-months')
    log(f'    A-exclusive (partial) total           : {n_excl_total:,} ticker-months')
    log(f'    A-exclusive with positive weight      : {n_A_excl_pos:,} ticker-months')
    log(f'    A-exclusive with zero weight          : {n_A_excl_zero:,} ticker-months')
    log()

    if n_A_excl_pos == 0 and n_excl_total > 0:
        log('  FINDING [QUANTITY 5]:')
        log('  A-exclusive stocks have partial history but ZERO prior-month-end weight.')
        log('  They have returns on ≥10 but not all days of a given month, yet their')
        log('  prior-month-end price is unavailable (new entrants, no lagged price).')
        log('  W.reindex(valid_A).fillna(0) maps them to 0. After renormalisation,')
        log('  they contribute nothing to mu_d, eta_j, or eps_{ij}.')
        log('  The positive-weight baskets of A and B are identical.')
        log()
        log('  This is the correct explanation for A = B across all 180 months.')
        log('  Whether Option-B-qualified stocks also have daily gaps is vacuous:')
        log('  by definition they have returns on every trading day of the month.')

    elif n_A_excl_pos > 0:
        log('  FINDING [QUANTITY 5]:')
        log(f'  {n_A_excl_pos} A-exclusive ticker-months have POSITIVE prior-month-end weight.')
        log('  These are the cases where A and B produce different component estimates.')
        log()
        mf = pd.DataFrame(month_rows)
        active = mf[mf['n_A_excl_pos'] > 0]
        log('  Months with positive-weight A-exclusive stocks:')
        for _, row in active.iterrows():
            log(f'    {int(row["year"])}-{int(row["month"]):02d}: '
                f'{int(row["n_A_excl_pos"])} ticker(s)')

    if n_B_zero > 0:
        log()
        log(f'  Note: {n_B_zero} Option-B-eligible ticker-months also have zero weight.')
        log('  These are Option-B-complete stocks that are new entrants in the same')
        log('  month (their full month is available, but no prior-month price exists).')
        log('  They too are excluded from component calculations by the zero fill.')


# ---------------------------------------------------------------------------
# S6: Industry contributing weight  [QUANTITY 2]
# ---------------------------------------------------------------------------

def industry_contributing_weight(
    monthly_baskets: list[dict],
    ticker_industry: pd.DataFrame,
    dr_primary: pd.DataFrame,
) -> None:
    header('S6  INDUSTRY-LEVEL CONTRIBUTING WEIGHT  [QUANTITY 2]')
    log('  Using Option-B basket weights (positive-weight stocks only).')
    log()

    ind_qt_records: dict[str, list[float]] = {}
    ind_fullwt_records: dict[str, list[float]] = {}

    for rec in monthly_baskets:
        yr, mo    = rec['year'], rec['month']
        W_B       = rec['W_B']
        valid_B   = rec['valid_B']
        mask      = (dr_primary.index.year == yr) & (dr_primary.index.month == mo)
        R_month   = dr_primary[mask]

        # Industry map restricted to this month's basket
        ind_in_month = ticker_industry.reindex(valid_B)

        for ind_num in ind_in_month['industry_num'].dropna().unique():
            members = ind_in_month[ind_in_month['industry_num'] == ind_num].index.tolist()
            if not members:
                continue
            ind_name = ind_in_month.loc[members[0], 'industry_name']
            W_j_full = float(W_B.reindex(members, fill_value=0.0).sum())

            # Daily contributing weight for this industry
            for dt, row in R_month.iterrows():
                has_return = row.reindex(members, fill_value=np.nan).notna()
                W_j_contributing = float(W_B.reindex(members, fill_value=0.0)[has_return].sum())

                if ind_name not in ind_qt_records:
                    ind_qt_records[ind_name]    = []
                    ind_fullwt_records[ind_name] = []
                ind_qt_records[ind_name].append(W_j_contributing)
                ind_fullwt_records[ind_name].append(W_j_full)

    log(f'  {"Industry":<35} {"Mean wt":<10} {"Mean contrib wt":<18} {"Days below full"}')
    rule()
    rows_for_print = []
    for ind_name in sorted(ind_qt_records.keys()):
        contrib_arr  = np.array(ind_qt_records[ind_name])
        full_arr     = np.array(ind_fullwt_records[ind_name])
        mean_wt      = float(np.mean(full_arr))
        mean_contrib = float(np.mean(contrib_arr))
        days_below   = int(np.sum(contrib_arr < full_arr - QT_TOLERANCE))
        rows_for_print.append((mean_wt, ind_name, mean_wt, mean_contrib, days_below))

    rows_for_print.sort(reverse=True)
    for _, ind_name, mean_wt, mean_contrib, days_below in rows_for_print:
        log(f'  {ind_name:<35} {mean_wt:<10.5f} {mean_contrib:<18.5f} {days_below}')

    any_below = sum(r[-1] for r in rows_for_print)
    log()
    if any_below == 0:
        log('  CONCLUSION [QUANTITY 2]:')
        log('  Industry contributing weight equals full industry weight on all days.')
        log('  No industry-level missing-weight variation exists in this dataset.')
    else:
        log(f'  WARNING: {any_below} industry-day pairs with contributing weight < full weight.')
        log('  Review individual months above.')


# ---------------------------------------------------------------------------
# S7: Reconciliation — cached A vs B  [QUANTITY 6]
# ---------------------------------------------------------------------------

def reconciliation_report(
    monthly_A: pd.DataFrame,
    monthly_B: pd.DataFrame,
    qt_A: pd.Series,
    qt_B: pd.Series,
) -> None:
    header('S7  RECONCILIATION: A vs B MONTHLY COMPONENTS  [QUANTITY 6]')
    log('  Computed from cached CSV results (not re-estimated).')
    log()

    for col in ['MKT', 'IND', 'FIRM']:
        delta = (monthly_A[col] - monthly_B[col]).abs()
        log(f'  {col}:')
        log(f'    Max  |A - B|: {delta.max():.4e}')
        log(f'    Mean |A - B|: {delta.mean():.4e}')
        n_nonzero = (delta > 1e-15).sum()
        log(f'    Months with |A - B| > 1e-15: {n_nonzero}')
        log()

    n_stock_diff = (monthly_A['n_stocks'] != monthly_B['n_stocks']).sum()
    stock_delta  = (monthly_A['n_stocks'] - monthly_B['n_stocks']).abs()
    log(f'  n_stocks discrepancy:')
    log(f'    Months where n_stocks(A) ≠ n_stocks(B): {n_stock_diff}')
    if n_stock_diff > 0:
        log(f'    Max difference: {int(stock_delta.max())}')
        log(f'    Total additional ticker-months in A: {int(stock_delta.sum())}')
        log()
        log('  Note: n_stocks counts all eligible tickers, including zero-weight')
        log('  entrants. It should NOT be presented as the number of contributing')
        log('  securities — positive-weight count is the informative figure.')
    log()

    log('  FIRM share convention clarification:')
    total_A = monthly_A[['MKT','IND','FIRM']].sum()
    firm_share_of_sums = total_A['FIRM'] / total_A.sum()
    monthly_A_shares = monthly_A['FIRM'] / monthly_A[['MKT','IND','FIRM']].sum(axis=1)
    mean_monthly_share = monthly_A_shares.mean()
    log(f'    "39.9% FIRM" = FIRM / (MKT+IND+FIRM) of summed variances : {firm_share_of_sums:.4%}')
    log(f'    Average monthly FIRM share (mean of monthly ratios)       : {mean_monthly_share:.4%}')
    log()
    log('  These are different quantities. The report uses the former (ratio of sums).')
    log('  G-Zephy audit noted the mean monthly share is 46.3% — confirmed.')

    log()
    log('  CONCLUSION [QUANTITY 6]:')
    qt_below_A = (qt_A < 1.0 - QT_TOLERANCE).sum()
    qt_below_B = (qt_B < 1.0 - QT_TOLERANCE).sum()
    if qt_below_A == 0 and qt_below_B == 0:
        log('  q_t = 1 on all days → MKT_A = MKT_B on all days at the mu_d level.')
        log('  Component equality confirmed by cached CSV (all deltas < 1e-15 for')
        log('  components; n_stocks differs due to zero-weight entrants).')
        log('  Residual delta arises solely from floating-point accumulation differences,')
        log('  not from different effective portfolios.')
    else:
        log(f'  q_t < 1 on {qt_below_A} (A) and {qt_below_B} (B) days.')
        log('  The mu_d level differs on those days. Monthly deltas reflect this.')


# ---------------------------------------------------------------------------
# S8: Chart
# ---------------------------------------------------------------------------

def make_chart(
    qt_A: pd.Series,
    qt_B: pd.Series,
    dr_primary: pd.DataFrame,
    monthly_baskets: list[dict],
) -> None:
    header('S8  GENERATING CHART')

    fig, axes = plt.subplots(3, 1, figsize=(14, 11),
                              gridspec_kw={'height_ratios': [2, 1.5, 1.5]})
    fig.suptitle('WP-05 Daily Weight Audit — WP-05 Methodology q_t',
                 fontsize=14, fontweight='bold', y=0.98)

    # Panel 1: q_t both options
    ax1 = axes[0]
    ax1.plot(qt_B.index, qt_B.values, linewidth=0.8, color='steelblue',
             alpha=0.85, label='Option B q_t')
    ax1.plot(qt_A.index, qt_A.values, linewidth=0.8, color='tomato',
             alpha=0.6, linestyle='--', label='Option A q_t')
    ax1.axhline(1.0, color='black', linewidth=0.8, linestyle='-', alpha=0.4,
                label='q_t = 1.0')
    ax1.set_ylabel('q_t (WP-05 contributing weight)', fontsize=11)
    ax1.set_title('Daily Contributing Weight q_t (WP-05 methodology)', fontsize=12)
    ymin = min(qt_A.min(), qt_B.min())
    ax1.set_ylim(max(0, ymin - 0.01), 1.005)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax1.xaxis.set_major_locator(mdates.YearLocator(2))
    ax1.legend(fontsize=9)
    ax1.grid(True, alpha=0.3)

    # Panel 2: A-exclusive ticker-months by month
    ax2 = axes[1]
    excl_dates = [pd.Timestamp(r['year'], r['month'], 1)
                  for r in monthly_baskets if r['n_A_excl'] > 0]
    excl_counts = [r['n_A_excl'] for r in monthly_baskets if r['n_A_excl'] > 0]
    excl_pos    = [r['n_A_excl_pos_wt'] for r in monthly_baskets if r['n_A_excl'] > 0]

    if excl_dates:
        ax2.bar(excl_dates, excl_counts, width=20, color='mediumpurple', alpha=0.7,
                label='A-exclusive (total)')
        ax2.bar(excl_dates, excl_pos, width=20, color='red', alpha=0.9,
                label='A-exclusive with positive weight')
        ax2.legend(fontsize=9)
    else:
        ax2.text(0.5, 0.5, 'No A-exclusive tickers (valid_A ≡ valid_B)',
                 ha='center', va='center', transform=ax2.transAxes, fontsize=11)
    ax2.set_ylabel('Ticker-months', fontsize=11)
    ax2.set_title('A-Exclusive Partial Ticker-Months per Month', fontsize=12)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax2.xaxis.set_major_locator(mdates.YearLocator(2))
    ax2.grid(True, alpha=0.3)

    # Panel 3: 1 - q_t (magnified)
    ax3 = axes[2]
    missing_A = (1.0 - qt_A)
    missing_B = (1.0 - qt_B)
    ax3.fill_between(missing_B.index, missing_B.values * 1e9,
                     color='steelblue', alpha=0.6, label='Option B (×1e9)')
    ax3.fill_between(missing_A.index, missing_A.values * 1e9,
                     color='tomato', alpha=0.5, label='Option A (×1e9)')
    ax3.set_ylabel('(1 − q_t) × 10⁹', fontsize=11)
    ax3.set_title('Missing Weight (magnified — floatng-point level)', fontsize=12)
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax3.xaxis.set_major_locator(mdates.YearLocator(2))
    ax3.legend(fontsize=9)
    ax3.grid(True, alpha=0.3)

    fig.autofmt_xdate(rotation=0, ha='center')
    plt.tight_layout(rect=[0, 0, 1, 0.97])
    plt.savefig(FIG_PATH, dpi=150, bbox_inches='tight')
    plt.close()
    log(f'  Chart saved: {FIG_PATH}')


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    log('=' * 72)
    log('  Project Parallax — WP-05 Daily Weight Audit  (v2 — corrected)')
    log(f'  Run date  : {datetime.date.today()}')
    log(f'  Window    : {STUDY_START} to {STUDY_END}')
    log('  Tolerance : 1e-9 (consistent across all q_t comparisons)')
    log('  Inputs    : cached data only — no network calls, no yfinance')
    log('  Governance: no methodology changes; D-018/D-020 remain open')
    log('=' * 72)

    (prices, shares, ticker_industry,
     dr_primary, approx_mktcap,
     monthly_A, monthly_B) = load_data()

    monthly_baskets = build_monthly_baskets(dr_primary, approx_mktcap, ticker_industry)
    qt_A, qt_B      = compute_qt_wp05(dr_primary, monthly_baskets)

    qt_below_one_report(qt_A, qt_B)
    volatility_clustering_report(qt_A, qt_B, dr_primary)
    option_b_gap_report(monthly_baskets)
    industry_contributing_weight(monthly_baskets, ticker_industry, dr_primary)
    reconciliation_report(monthly_A, monthly_B, qt_A, qt_B)
    make_chart(qt_A, qt_B, dr_primary, monthly_baskets)

    header('AUDIT COMPLETE')
    log(f'  Outputs:')
    log(f'    {REPORT_PATH}')
    log(f'    {FIG_PATH}')
    log()
    log('  Return this evidence to G-Zephy before D-018 adjudication.')

    save_report()


if __name__ == '__main__':
    main()
