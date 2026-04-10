"""Reporting module for live signal generation."""

import pandas as pd
from typing import Dict
from pathlib import Path
from tabulate import tabulate
import logging

from . import config

logger = logging.getLogger(__name__)


def generate_signal_report(
    portfolio: Dict,
    output_dir: Path,
    etf_universe: Dict[str, str],
) -> pd.DataFrame:
    """
    Generate current signals report.

    Args:
        portfolio: Portfolio recommendations dictionary
        output_dir: Directory to save output
        etf_universe: Dictionary mapping ticker to ETF name

    Returns:
        DataFrame with signal recommendations
    """
    rows = []

    for etf in portfolio['selected_etfs']:
        rows.append({
            'Rank': etf['rank'],
            'ETF': etf['ticker'],
            'Country/Region': etf_universe.get(etf['ticker'], 'Unknown'),
            'Mom. Quality': f"{etf['momentum_quality']:.2f}",
            'RS ROC (%)': f"{etf['rs_roc'] * 100:.2f}",
            'Allocation (%)': f"{etf['weight'] * 100:.0f}",
        })

    df = pd.DataFrame(rows)

    # Add SPY row if applicable
    if portfolio['spy_allocation'] > 0:
        spy_row = pd.DataFrame([{
            'Rank': '-',
            'ETF': 'SPY',
            'Country/Region': 'S&P 500 (Fallback)',
            'RS ROC (%)': '-',
            'Allocation (%)': f"{portfolio['spy_allocation'] * 100:.0f}",
        }])
        df = pd.concat([df, spy_row], ignore_index=True)

    # Save to CSV
    output_path = output_dir / 'current_signals.csv'
    df.to_csv(output_path, index=False)
    logger.info(f"Saved current signals to {output_path}")

    return df


def generate_detailed_status_report(
    status: pd.DataFrame,
    output_dir: Path,
    etf_universe: Dict[str, str],
) -> pd.DataFrame:
    """
    Generate detailed status report for all ETFs.

    Args:
        status: DataFrame with all ETF status
        output_dir: Directory to save output
        etf_universe: Dictionary mapping ticker to ETF name

    Returns:
        DataFrame with detailed status
    """
    # Add country names
    status['country'] = status['ticker'].map(etf_universe)

    # Reorder and format columns
    df = status[['ticker', 'country', 'price', 'price_sma', 'rs_ratio', 'rs_sma',
                 'rs_filter', 'abs_filter', 'momentum_quality', 'rs_roc', 'rank']].copy()

    df.columns = ['Ticker', 'Country/Region', 'Price', 'Price SMA', 'RS Ratio',
                  'RS SMA', 'RS Filter', 'Abs Filter', 'Mom. Quality', 'RS ROC', 'Rank']

    # Format numeric columns
    for col in ['Price', 'Price SMA', 'RS Ratio', 'RS SMA', 'Mom. Quality', 'RS ROC']:
        df[col] = df[col].round(4)

    # Format filters as PASS/FAIL
    df['RS Filter'] = df['RS Filter'].map({True: 'PASS ✓', False: 'FAIL ✗'})
    df['Abs Filter'] = df['Abs Filter'].map({True: 'PASS ✓', False: 'FAIL ✗'})

    # Save to CSV
    output_path = output_dir / 'all_etf_status.csv'
    df.to_csv(output_path, index=False)
    logger.info(f"Saved detailed status to {output_path}")

    return df


def print_signal_report(portfolio: Dict, df: pd.DataFrame) -> None:
    """
    Print signal report to console.

    Args:
        portfolio: Portfolio recommendations dictionary
        df: DataFrame with recommendations
    """
    date = portfolio['date']
    qualifying_count = portfolio['qualifying_count']

    print("\n" + "="*70)
    print("MONTHLY PORTFOLIO RECOMMENDATIONS")
    print("="*70)
    print(f"Generated: {date.strftime('%B %d, %Y')}")
    print(f"For Period: {date.strftime('%B %Y')}")
    print("="*70)

    print("\nRECOMMENDED HOLDINGS:")
    print(tabulate(df, headers='keys', tablefmt='grid', showindex=False))

    print(f"\nTotal Qualifying ETFs: {qualifying_count}")
    print(f"Selected for Portfolio: {len(portfolio['selected_etfs'])}")

    if portfolio['spy_allocation'] > 0:
        print(f"SPY Fallback Allocation: {portfolio['spy_allocation']*100:.0f}%")

    print("="*70 + "\n")


def print_detailed_status(df: pd.DataFrame, top_n: int = 10) -> None:
    """
    Print detailed status of top ETFs.

    Args:
        df: DataFrame with detailed status
        top_n: Number of top ETFs to display
    """
    print("\n" + "="*70)
    print(f"TOP {top_n} ETF SIGNALS (Ranked by RS Momentum)")
    print("="*70)

    # Show top N
    top_df = df.head(top_n)
    print(tabulate(top_df, headers='keys', tablefmt='grid', showindex=False))

    print("="*70 + "\n")


def print_summary_stats(portfolio: Dict, signals: Dict) -> None:
    """
    Print summary statistics about current signals.

    Args:
        portfolio: Portfolio recommendations
        signals: All signals dictionary
    """
    total_etfs = len(signals)
    qualifying = portfolio['qualifying_count']
    selected = len(portfolio['selected_etfs'])

    print("\n" + "="*70)
    print("SIGNAL SUMMARY")
    print("="*70)
    print(f"Total ETFs Analyzed: {total_etfs}")

    if total_etfs > 0:
        print(f"ETFs Passing Both Filters: {qualifying} ({qualifying/total_etfs*100:.1f}%)")
    else:
        print(f"ETFs Passing Both Filters: {qualifying}")

    print(f"ETFs Selected for Portfolio: {selected}")
    print(f"Portfolio Concentration: {selected}/{5} positions filled")

    if qualifying > 5:
        print(f"\nNote: {qualifying - 5} additional ETFs qualified but not selected")
        print("(Ranked lower by RS momentum)")

    print("="*70 + "\n")
