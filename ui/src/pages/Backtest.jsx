import { useState } from 'react'
import { backtestAPI } from '../services/api'
import './Backtest.css'

function Backtest() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [results, setResults] = useState(null)

  const [formData, setFormData] = useState({
    universe: 'sp500',
    start_date: '2016-01-01',
    end_date: '2026-01-01',
    refresh: false,
  })

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setResults(null)

    try {
      const result = await backtestAPI.runBacktest(formData)
      setResults(result)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const formatNumber = (num, decimals = 2) => {
    if (num === null || num === undefined) return 'N/A'
    return Number(num).toFixed(decimals)
  }

  const formatPercent = (num, decimals = 2) => {
    if (num === null || num === undefined) return 'N/A'
    const value = Number(num).toFixed(decimals)
    return `${value}%`
  }

  const getChangeClass = (value) => {
    if (value > 0) return 'positive'
    if (value < 0) return 'negative'
    return ''
  }

  return (
    <div className="container">
      <div className="page-header">
        <h1 className="page-title">Backtest Engine</h1>
        <p className="page-description">
          Run historical backtests to evaluate strategy performance
        </p>
      </div>

      {/* Configuration Form */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Backtest Configuration</h2>
          <p className="card-subtitle">Set parameters for backtest simulation</p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="grid grid-3">
            <div className="form-group">
              <label className="form-label">ETF Universe</label>
              <select
                name="universe"
                className="form-select"
                value={formData.universe}
                onChange={handleInputChange}
                disabled={loading}
              >
                <option value="sp500">S&P 500 Sector ETFs (11 sectors)</option>
                <option value="developed">Developed Market ETFs</option>
                <option value="emerging">Emerging Market ETFs</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Start Date</label>
              <input
                type="date"
                name="start_date"
                className="form-input"
                value={formData.start_date}
                onChange={handleInputChange}
                disabled={loading}
              />
              <small className="text-muted">Recommended: 2016-01-01 (10 years)</small>
            </div>

            <div className="form-group">
              <label className="form-label">End Date</label>
              <input
                type="date"
                name="end_date"
                className="form-input"
                value={formData.end_date}
                onChange={handleInputChange}
                disabled={loading}
              />
              <small className="text-muted">Recommended: 2026-01-01</small>
            </div>
          </div>

          <div className="form-group">
            <div className="form-checkbox">
              <input
                type="checkbox"
                id="refresh"
                name="refresh"
                checked={formData.refresh}
                onChange={handleInputChange}
                disabled={loading}
              />
              <label htmlFor="refresh">Refresh data from API (fetch latest prices)</label>
            </div>
          </div>

          <div className="form-actions">
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
            >
              {loading ? 'Running Backtest...' : 'Run Backtest'}
            </button>
          </div>
        </form>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="card">
          <div className="loading-container">
            <div className="spinner"></div>
            <p>Running backtest... This may take up to 2 minutes for large datasets.</p>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="alert alert-error">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Results */}
      {results && !loading && (
        <>
          {/* Success Message */}
          <div className="alert alert-success">
            <strong>Success!</strong> Backtest completed for {results.universe} from {results.period?.start} to {results.period?.end}.
          </div>

          {/* Performance Summary */}
          {results.performance && (
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">Performance Summary</h2>
                <p className="card-subtitle">
                  {results.period?.years} year backtest results
                </p>
              </div>

              <div className="grid grid-4">
                <div className="stat-card">
                  <div className="stat-label">Total Return</div>
                  <div className={`stat-value ${getChangeClass(results.performance.total_return)}`}>
                    {formatPercent(results.performance.total_return, 2)}
                  </div>
                  {results.performance.annualized_return && (
                    <div className="stat-change text-muted">
                      {formatPercent(results.performance.annualized_return, 2)} annualized
                    </div>
                  )}
                </div>

                <div className="stat-card">
                  <div className="stat-label">Sharpe Ratio</div>
                  <div className="stat-value">
                    {formatNumber(results.performance.sharpe_ratio, 3)}
                  </div>
                  <div className="stat-change text-muted">
                    {results.performance.sharpe_ratio > 1 ? 'Excellent' :
                     results.performance.sharpe_ratio > 0.5 ? 'Good' : 'Fair'}
                  </div>
                </div>

                <div className="stat-card">
                  <div className="stat-label">Max Drawdown</div>
                  <div className="stat-value text-danger">
                    {formatPercent(results.performance.max_drawdown, 2)}
                  </div>
                </div>

                <div className="stat-card">
                  <div className="stat-label">vs SPY</div>
                  <div className={`stat-value ${getChangeClass(results.performance.vs_spy)}`}>
                    {results.performance.vs_spy > 0 ? '+' : ''}
                    {formatPercent(results.performance.vs_spy, 2)}
                  </div>
                  <div className={`stat-change ${getChangeClass(results.performance.vs_spy)}`}>
                    {results.performance.vs_spy > 0 ? 'Outperformance' : 'Underperformance'}
                  </div>
                </div>
              </div>

              {/* SPY Benchmark Comparison */}
              {results.benchmark && (
                <div className="benchmark-comparison">
                  <h3 className="section-title">Benchmark Comparison</h3>
                  <div className="grid grid-2">
                    <div className="comparison-card">
                      <h4 className="comparison-title">Strategy</h4>
                      <div className="comparison-stats">
                        <div className="comparison-stat">
                          <span className="comparison-label">Total Return:</span>
                          <span className={`comparison-value ${getChangeClass(results.performance.total_return)}`}>
                            {formatPercent(results.performance.total_return)}
                          </span>
                        </div>
                        <div className="comparison-stat">
                          <span className="comparison-label">Sharpe Ratio:</span>
                          <span className="comparison-value">
                            {formatNumber(results.performance.sharpe_ratio, 3)}
                          </span>
                        </div>
                        <div className="comparison-stat">
                          <span className="comparison-label">Max Drawdown:</span>
                          <span className="comparison-value text-danger">
                            {formatPercent(results.performance.max_drawdown)}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="comparison-card">
                      <h4 className="comparison-title">SPY Benchmark</h4>
                      <div className="comparison-stats">
                        <div className="comparison-stat">
                          <span className="comparison-label">Total Return:</span>
                          <span className={`comparison-value ${getChangeClass(results.benchmark.total_return)}`}>
                            {formatPercent(results.benchmark.total_return)}
                          </span>
                        </div>
                        <div className="comparison-stat">
                          <span className="comparison-label">Sharpe Ratio:</span>
                          <span className="comparison-value">
                            {formatNumber(results.benchmark.sharpe_ratio, 3)}
                          </span>
                        </div>
                        <div className="comparison-stat">
                          <span className="comparison-label">Max Drawdown:</span>
                          <span className="comparison-value text-danger">
                            {formatPercent(results.benchmark.max_drawdown)}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Yearly Returns */}
          {results.yearly_returns && results.yearly_returns.length > 0 && (
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">Yearly Returns</h2>
                <p className="card-subtitle">Year-by-year performance breakdown</p>
              </div>

              <div className="table-container">
                <table>
                  <thead>
                    <tr>
                      <th>Year</th>
                      <th className="text-right">Strategy Return</th>
                      <th className="text-right">SPY Return</th>
                      <th className="text-right">Outperformance</th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.yearly_returns.map((year) => (
                      <tr key={year.year}>
                        <td className="text-bold">{year.year}</td>
                        <td className={`text-right ${getChangeClass(year.strategy_return)}`}>
                          {formatPercent(year.strategy_return)}
                        </td>
                        <td className={`text-right ${getChangeClass(year.spy_return)}`}>
                          {formatPercent(year.spy_return)}
                        </td>
                        <td className={`text-right ${getChangeClass(year.outperformance)}`}>
                          {year.outperformance > 0 ? '+' : ''}
                          {formatPercent(year.outperformance)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Portfolio Composition Sample */}
          {results.portfolio_sample && results.portfolio_sample.length > 0 && (
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">Sample Portfolio Allocations</h2>
                <p className="card-subtitle">Recent monthly rebalancing history (last 6 periods)</p>
              </div>

              <div className="table-container">
                <table>
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Holdings</th>
                      <th className="text-right">Portfolio Value</th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.portfolio_sample.map((entry, index) => (
                      <tr key={index}>
                        <td className="text-bold">{entry.date}</td>
                        <td>
                          <div className="holdings-list">
                            {entry.holdings.map((holding, i) => (
                              <span key={i} className="holding-badge">
                                {holding}
                              </span>
                            ))}
                          </div>
                        </td>
                        <td className="text-right">
                          ${formatNumber(entry.portfolio_value, 2)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Parameters Used */}
          {results.parameters && (
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">Parameters Used</h2>
              </div>

              <div className="grid grid-4">
                <div className="stat-card">
                  <div className="stat-label">Top N Holdings</div>
                  <div className="stat-value">{results.parameters.top_n}</div>
                </div>

                <div className="stat-card">
                  <div className="stat-label">SMA Lookback</div>
                  <div className="stat-value">{results.parameters.sma_days}</div>
                  <div className="text-muted" style={{ fontSize: '0.75rem', marginTop: '0.25rem' }}>
                    days (~{Math.round(results.parameters.sma_days / 21)} months)
                  </div>
                </div>

                <div className="stat-card">
                  <div className="stat-label">ROC Lookback</div>
                  <div className="stat-value">{results.parameters.roc_days}</div>
                  <div className="text-muted" style={{ fontSize: '0.75rem', marginTop: '0.25rem' }}>
                    days (~{Math.round(results.parameters.roc_days / 21)} months)
                  </div>
                </div>

                <div className="stat-card">
                  <div className="stat-label">Rebalance Frequency</div>
                  <div className="stat-value" style={{ fontSize: '1.25rem' }}>
                    {results.parameters.rebalance_freq}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Timestamp */}
          {results.timestamp && (
            <div className="text-center text-muted" style={{ fontSize: '0.875rem', marginTop: '2rem' }}>
              Backtest completed: {new Date(results.timestamp).toLocaleString()}
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default Backtest
