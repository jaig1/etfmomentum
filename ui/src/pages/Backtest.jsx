import { useState, useEffect } from 'react'
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
    initial_capital: 100000,
    top_n: 3,
    rebalance_frequency: 'weekly',
    enable_volatility_regime: true,
    refresh_data: false,
  })

  // Debug logging
  useEffect(() => {
    console.log('🎨 Backtest state:', { loading, hasResults: !!results, hasError: !!error })
  }, [loading, results, error])

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    console.log('📊 Running backtest with params:', formData)
    setLoading(true)
    setError(null)
    setResults(null)

    try {
      const result = await backtestAPI.runBacktest(formData)
      console.log('✅ Backtest results received:', result)
      setResults(result)
      setLoading(false)
    } catch (err) {
      console.error('❌ Backtest error:', err)
      setError(err.message)
      setLoading(false)
    }
  }

  const formatNumber = (num, decimals = 2) => {
    if (num === null || num === undefined || isNaN(num)) return 'N/A'
    return Number(num).toFixed(decimals)
  }

  const formatPercent = (num, decimals = 2) => {
    if (num === null || num === undefined || isNaN(num)) return 'N/A'
    const value = Number(num).toFixed(decimals)
    return `${value}%`
  }

  const formatCurrency = (num) => {
    if (num === null || num === undefined || isNaN(num)) return 'N/A'
    return `$${Number(num).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  }

  const getChangeClass = (value) => {
    if (value > 0) return 'positive'
    if (value < 0) return 'negative'
    return ''
  }

  const calculateYears = () => {
    if (!results) return 0
    const start = new Date(results.start_date)
    const end = new Date(results.end_date)
    return ((end - start) / (365.25 * 24 * 60 * 60 * 1000)).toFixed(1)
  }

  console.log('🎨 Rendering Backtest component')

  return (
    <div className="container">
      <div className="page-header">
        <h1 className="page-title">Backtest Engine</h1>
        <p className="page-description">
          Run historical backtests with weekly rebalancing - Strategy vs SPY Buy & Hold
        </p>
      </div>

      {/* Simulation Info Banner */}
      <div className="alert alert-info" style={{ marginBottom: '1.5rem' }}>
        <strong>📊 Backtest Simulation:</strong> Tests the strategy over your selected date range with weekly rebalancing.
        Compares top N ETF momentum portfolio vs SPY buy-and-hold benchmark using the same initial capital.
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
                <option value="emerging">Emerging Market ETFs</option>
                <option value="developed">Developed Market ETFs</option>
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
              <small className="text-muted">Latest: 2026-03-16</small>
            </div>
          </div>

          <div className="grid grid-2">
            <div className="form-group">
              <label className="form-label">Initial Capital ($)</label>
              <input
                type="number"
                name="initial_capital"
                className="form-input"
                value={formData.initial_capital}
                onChange={handleInputChange}
                disabled={loading}
                min="1000"
                step="1000"
              />
            </div>

            <div className="form-group">
              <label className="form-label">Top N Holdings</label>
              <select
                name="top_n"
                className="form-select"
                value={formData.top_n}
                onChange={handleInputChange}
                disabled={loading}
              >
                <option value="3">3 (Recommended - Best Sharpe)</option>
                <option value="5">5</option>
                <option value="7">7</option>
                <option value="10">10</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <div className="form-checkbox">
              <input
                type="checkbox"
                id="refresh_data"
                name="refresh_data"
                checked={formData.refresh_data}
                onChange={handleInputChange}
                disabled={loading}
              />
              <label htmlFor="refresh_data">Refresh data from API (fetch latest prices)</label>
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
      {error && !loading && (
        <div className="alert alert-error">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Results */}
      {results && !loading && (
        <>
          {/* Success Message */}
          <div className="alert alert-success">
            <strong>Success!</strong> Backtest completed for {results.universe} from {results.start_date} to {results.end_date} ({calculateYears()} years).
          </div>

          {/* Performance Summary */}
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">📈 Backtest Results Summary</h2>
              <p className="card-subtitle">
                {calculateYears()} year backtest - Initial Capital: {formatCurrency(formData.initial_capital)}
              </p>
            </div>

            <div className="grid grid-3">
              <div className="metric-card">
                <div className="metric-label">Strategy Final Value</div>
                <div className="metric-value">
                  {formatCurrency(results.final_value)}
                </div>
                <div className={`metric-change ${getChangeClass(results.total_return)}`}>
                  {formatPercent(results.total_return)} total return
                </div>
              </div>

              <div className="metric-card">
                <div className="metric-label">SPY Final Value</div>
                <div className="metric-value">
                  {formatCurrency(results.spy_final_value)}
                </div>
                <div className={`metric-change ${getChangeClass(results.spy_total_return)}`}>
                  {formatPercent(results.spy_total_return)} total return
                </div>
              </div>

              <div className="metric-card">
                <div className="metric-label">Strategy vs SPY</div>
                <div className={`metric-value ${getChangeClass(results.outperformance)}`}>
                  {results.outperformance > 0 ? '+' : ''}{formatPercent(results.outperformance, 2)}
                </div>
                <div className={`metric-change ${getChangeClass(results.final_value - results.spy_final_value)}`}>
                  {formatCurrency(results.final_value - results.spy_final_value)} difference
                </div>
              </div>
            </div>

            <div className="grid grid-3" style={{ marginTop: '1rem' }}>
              <div className="metric-card">
                <div className="metric-label">Annualized Return</div>
                <div className={`metric-value ${getChangeClass(results.annualized_return)}`}>
                  {formatPercent(results.annualized_return, 2)}
                </div>
                <div className="metric-subtext">Strategy per year</div>
              </div>

              <div className="metric-card">
                <div className="metric-label">Sharpe Ratio</div>
                <div className="metric-value">
                  {formatNumber(results.sharpe_ratio, 3)}
                </div>
                <div className="metric-subtext">
                  {results.sharpe_ratio > 1 ? 'Excellent' :
                   results.sharpe_ratio > 0.5 ? 'Good' : 'Fair'} risk-adjusted return
                </div>
              </div>

              <div className="metric-card">
                <div className="metric-label">Max Drawdown</div>
                <div className="metric-value negative">
                  {formatPercent(results.max_drawdown, 2)}
                </div>
                <div className="metric-subtext">Largest peak-to-trough decline</div>
              </div>
            </div>

            <div className="grid grid-2" style={{ marginTop: '1rem' }}>
              <div className="metric-card">
                <div className="metric-label">Win Rate</div>
                <div className="metric-value">
                  {formatPercent(results.win_rate, 1)}
                </div>
                <div className="metric-subtext">Years outperforming SPY</div>
              </div>

              <div className="metric-card">
                <div className="metric-label">SPY Sharpe Ratio</div>
                <div className="metric-value">
                  {formatNumber(results.spy_sharpe_ratio, 3)}
                </div>
                <div className="metric-subtext">Benchmark risk-adjusted return</div>
              </div>
            </div>
          </div>

          {/* Yearly Returns */}
          {results.yearly_breakdown && results.yearly_breakdown.length > 0 && (
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">📊 Yearly Performance Breakdown</h2>
                <p className="card-subtitle">Year-by-year comparison of strategy vs SPY</p>
              </div>

              <div className="table-container">
                <table>
                  <thead>
                    <tr>
                      <th>Year</th>
                      <th className="text-right">Strategy Return</th>
                      <th className="text-right">SPY Return</th>
                      <th className="text-right">Outperformance</th>
                      <th className="text-center">Result</th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.yearly_breakdown.map((year) => (
                      <tr key={year.year}>
                        <td className="text-bold">{year.year}</td>
                        <td className={`text-right ${getChangeClass(year.strategy_return)}`}>
                          {formatPercent(year.strategy_return, 2)}
                        </td>
                        <td className={`text-right ${getChangeClass(year.spy_return)}`}>
                          {formatPercent(year.spy_return, 2)}
                        </td>
                        <td className={`text-right ${getChangeClass(year.outperformance)}`}>
                          {year.outperformance > 0 ? '+' : ''}{formatPercent(year.outperformance, 2)}
                        </td>
                        <td className="text-center">
                          <span className={`badge ${year.outperformance > 0 ? 'badge-success' : 'badge-danger'}`}>
                            {year.outperformance > 0 ? 'Win' : 'Loss'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Strategy Parameters */}
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">⚙️ Strategy Parameters</h2>
              <p className="card-subtitle">Configuration used for this backtest</p>
            </div>

            <div className="grid grid-4">
              <div className="stat-card">
                <div className="stat-label">ETF Universe</div>
                <div className="stat-value" style={{ fontSize: '1.25rem' }}>{results.universe}</div>
              </div>

              <div className="stat-card">
                <div className="stat-label">Top N Holdings</div>
                <div className="stat-value">{formData.top_n}</div>
                <div className="text-muted" style={{ fontSize: '0.75rem', marginTop: '0.25rem' }}>
                  Equal weight allocation
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-label">Rebalance Frequency</div>
                <div className="stat-value" style={{ fontSize: '1.25rem' }}>
                  {formData.rebalance_frequency}
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-label">Initial Capital</div>
                <div className="stat-value" style={{ fontSize: '1.25rem' }}>
                  {formatCurrency(formData.initial_capital)}
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export default Backtest
