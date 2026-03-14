"""Performance metrics calculation and report generation."""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from pathlib import Path
from tabulate import tabulate
import logging

from .rs_engine import get_all_etf_status

logger = logging.getLogger(__name__)


def calculate_metrics(
    portfolio_values: pd.Series,
    initial_capital: float,
    risk_free_rate: float,
) -> Dict[str, float]:
    """
    Calculate performance metrics.

    Args:
        portfolio_values: Series of daily portfolio values
        initial_capital: Starting capital
        risk_free_rate: Annual risk-free rate (as decimal, e.g., 0.045 for 4.5%)

    Returns:
        Dictionary of performance metrics
    """
    # Total return
    final_value = portfolio_values.iloc[-1]
    total_return = (final_value - initial_capital) / initial_capital

    # Annualized return
    n_days = len(portfolio_values)
    n_years = n_days / 252  # 252 trading days per year
    annualized_return = (1 + total_return) ** (1 / n_years) - 1 if n_years > 0 else 0

    # Daily returns
    daily_returns = portfolio_values.pct_change().dropna()

    # Maximum drawdown
    cumulative_max = portfolio_values.expanding().max()
    drawdowns = (portfolio_values - cumulative_max) / cumulative_max
    max_drawdown = drawdowns.min()

    # Sharpe ratio (annualized)
    if len(daily_returns) > 1:
        excess_returns = daily_returns - (risk_free_rate / 252)  # Daily risk-free rate
        sharpe_ratio = np.sqrt(252) * excess_returns.mean() / daily_returns.std()
    else:
        sharpe_ratio = 0.0

    return {
        'total_return': total_return,
        'annualized_return': annualized_return,
        'max_drawdown': max_drawdown,
        'sharpe_ratio': sharpe_ratio,
        'final_value': final_value,
    }


def calculate_monthly_returns(portfolio_values: pd.Series) -> pd.DataFrame:
    """
    Calculate monthly returns.

    Args:
        portfolio_values: Series of daily portfolio values

    Returns:
        DataFrame with monthly returns
    """
    # Get month-end values
    monthly_values = portfolio_values.resample('ME').last()

    # Calculate returns
    monthly_returns = monthly_values.pct_change()

    # Create DataFrame with month names
    df = pd.DataFrame({
        'month': monthly_returns.index.strftime('%B %Y'),
        'return': monthly_returns.values,
    })

    return df.dropna()


def calculate_yearly_returns(portfolio_values: pd.Series) -> pd.DataFrame:
    """
    Calculate yearly returns.

    Args:
        portfolio_values: Series of daily portfolio values

    Returns:
        DataFrame with yearly returns
    """
    # Get year-end values
    yearly_values = portfolio_values.resample('YE').last()

    # Calculate returns
    yearly_returns = yearly_values.pct_change()

    # Create DataFrame with year
    df = pd.DataFrame({
        'year': yearly_returns.index.year,
        'return': yearly_returns.values,
    })

    return df.dropna()


def generate_performance_summary(
    strategy_metrics: Dict[str, float],
    benchmark_metrics: Dict[str, float],
    output_dir: Path,
) -> pd.DataFrame:
    """
    Generate performance summary table.

    Args:
        strategy_metrics: Metrics for the strategy
        benchmark_metrics: Metrics for the benchmark
        output_dir: Directory to save output

    Returns:
        DataFrame with performance summary
    """
    summary_data = {
        'Metric': [
            'Total Return (%)',
            'Annualized Return (%)',
            'Maximum Drawdown (%)',
            'Sharpe Ratio',
            'Final Value ($)',
        ],
        'Strategy': [
            f"{strategy_metrics['total_return'] * 100:.2f}",
            f"{strategy_metrics['annualized_return'] * 100:.2f}",
            f"{strategy_metrics['max_drawdown'] * 100:.2f}",
            f"{strategy_metrics['sharpe_ratio']:.3f}",
            f"{strategy_metrics['final_value']:,.2f}",
        ],
        'SPY (Buy & Hold)': [
            f"{benchmark_metrics['total_return'] * 100:.2f}",
            f"{benchmark_metrics['annualized_return'] * 100:.2f}",
            f"{benchmark_metrics['max_drawdown'] * 100:.2f}",
            f"{benchmark_metrics['sharpe_ratio']:.3f}",
            f"{benchmark_metrics['final_value']:,.2f}",
        ],
    }

    df = pd.DataFrame(summary_data)

    # Save to CSV
    output_path = output_dir / 'performance_summary.csv'
    df.to_csv(output_path, index=False)
    logger.info(f"Saved performance summary to {output_path}")

    return df


def generate_monthly_returns_table(
    strategy_values: pd.Series,
    benchmark_values: pd.Series,
    output_dir: Path,
) -> pd.DataFrame:
    """
    Generate monthly returns breakdown table.

    Args:
        strategy_values: Strategy portfolio values
        benchmark_values: Benchmark portfolio values
        output_dir: Directory to save output

    Returns:
        DataFrame with monthly returns
    """
    strategy_monthly = calculate_monthly_returns(strategy_values)
    benchmark_monthly = calculate_monthly_returns(benchmark_values)

    # Merge
    df = pd.DataFrame({
        'Month': strategy_monthly['month'].values,
        'Strategy Return (%)': (strategy_monthly['return'].values * 100).round(2),
        'SPY Return (%)': (benchmark_monthly['return'].values * 100).round(2),
    })

    df['Outperformance (%)'] = (df['Strategy Return (%)'] - df['SPY Return (%)']).round(2)

    # Calculate win rate
    wins = (df['Outperformance (%)'] > 0).sum()
    total = len(df)
    win_rate = f"{wins}/{total}"

    # Save to CSV
    output_path = output_dir / 'monthly_returns.csv'
    df.to_csv(output_path, index=False)
    logger.info(f"Saved monthly returns to {output_path}")

    return df, win_rate


def generate_yearly_summary_table(
    strategy_values: pd.Series,
    benchmark_values: pd.Series,
    output_dir: Path,
) -> pd.DataFrame:
    """
    Generate yearly returns summary table.

    Args:
        strategy_values: Strategy portfolio values
        benchmark_values: Benchmark portfolio values
        output_dir: Directory to save output

    Returns:
        DataFrame with yearly returns and win rate
    """
    strategy_yearly = calculate_yearly_returns(strategy_values)
    benchmark_yearly = calculate_yearly_returns(benchmark_values)

    # Merge
    df = pd.DataFrame({
        'Year': strategy_yearly['year'].values.astype(int),
        'Strategy Return (%)': (strategy_yearly['return'].values * 100).round(2),
        'SPY Return (%)': (benchmark_yearly['return'].values * 100).round(2),
    })

    df['Outperformance (%)'] = (df['Strategy Return (%)'] - df['SPY Return (%)']).round(2)

    # Calculate win rate
    wins = (df['Outperformance (%)'] > 0).sum()
    total = len(df)
    win_rate = f"{wins}/{total}"

    # Save to CSV
    output_path = output_dir / 'yearly_returns.csv'
    df.to_csv(output_path, index=False)
    logger.info(f"Saved yearly returns to {output_path}")

    return df, win_rate


def generate_portfolio_composition_log(
    rebalance_log: List[Dict],
    output_dir: Path,
    top_n: int,
) -> pd.DataFrame:
    """
    Generate portfolio composition log by calendar month.

    Args:
        rebalance_log: List of rebalance information dicts
        output_dir: Directory to save output
        top_n: Number of top holdings

    Returns:
        DataFrame with portfolio composition for each calendar month
    """
    rows = []

    # Map each rebalance to its calendar month
    for i, entry in enumerate(rebalance_log):
        date = entry['date']
        weights = entry['weights']

        # Separate ETFs and SPY
        etf_holdings = {k: v for k, v in weights.items() if k != 'SPY'}
        spy_weight = weights.get('SPY', 0.0)

        # Get the month name for this rebalance
        month_name = date.strftime('%B %Y')

        # Create row
        row = {'Month': month_name}

        # Add top N columns
        etf_list = sorted(etf_holdings.items(), key=lambda x: x[1], reverse=True)
        for j in range(top_n):
            col_name = f'ETF {j+1}'
            if j < len(etf_list):
                ticker, weight = etf_list[j]
                row[col_name] = f"{ticker} ({weight*100:.0f}%)"
            else:
                row[col_name] = ''

        row['SPY Allocation (%)'] = f"{spy_weight * 100:.0f}"

        rows.append(row)

    df = pd.DataFrame(rows)

    # Save to CSV
    output_path = output_dir / 'portfolio_composition.csv'
    df.to_csv(output_path, index=False)
    logger.info(f"Saved portfolio composition to {output_path}")

    return df


def generate_signal_status_report(
    signals: Dict[str, pd.DataFrame],
    rebalance_dates: List,
    output_dir: Path,
) -> None:
    """
    Generate signal status report for each rebalance date.

    Args:
        signals: Dictionary of signals DataFrames for each ETF
        rebalance_dates: List of rebalance dates
        output_dir: Directory to save output
    """
    all_status = []

    for date in rebalance_dates:
        df_status = get_all_etf_status(signals, date)
        df_status['date'] = date.strftime('%Y-%m-%d')
        all_status.append(df_status)

    # Combine all dates
    df_combined = pd.concat(all_status, ignore_index=True)

    # Reorder columns
    df_combined = df_combined[[
        'date', 'ticker', 'price', 'price_sma', 'rs_ratio', 'rs_sma',
        'rs_filter', 'abs_filter', 'rs_roc', 'rank'
    ]]

    # Round numeric columns
    numeric_cols = ['price', 'price_sma', 'rs_ratio', 'rs_sma', 'rs_roc']
    for col in numeric_cols:
        df_combined[col] = df_combined[col].round(4)

    # Save to CSV
    output_path = output_dir / 'signal_status.csv'
    df_combined.to_csv(output_path, index=False)
    logger.info(f"Saved signal status to {output_path}")


def print_performance_summary(df: pd.DataFrame, win_rate: str = None) -> None:
    """Print performance summary table to console."""
    print("\n" + "="*70)
    print("PERFORMANCE SUMMARY")
    print("="*70)
    print(tabulate(df, headers='keys', tablefmt='grid', showindex=False))
    if win_rate:
        print(f"\nWin Rate (months beating SPY): {win_rate}")
    print("="*70 + "\n")


def print_monthly_returns(df: pd.DataFrame) -> None:
    """Print monthly returns table to console."""
    print("\n" + "="*70)
    print("MONTHLY RETURNS BREAKDOWN")
    print("="*70)
    print(tabulate(df, headers='keys', tablefmt='grid', showindex=False))
    print("="*70 + "\n")


def print_portfolio_composition(df: pd.DataFrame) -> None:
    """Print portfolio composition table to console."""
    print("\n" + "="*70)
    print("PORTFOLIO COMPOSITION AT EACH REBALANCE")
    print("="*70)
    print(tabulate(df, headers='keys', tablefmt='grid', showindex=False))
    print("="*70 + "\n")


def print_yearly_summary(df: pd.DataFrame, win_rate: str = None) -> None:
    """Print yearly returns summary table to console."""
    print("\n" + "="*70)
    print("YEARLY RETURNS SUMMARY")
    print("="*70)
    print(tabulate(df, headers='keys', tablefmt='grid', showindex=False))
    if win_rate:
        print(f"\nWin Rate (years beating SPY): {win_rate}")
    print("="*70 + "\n")
