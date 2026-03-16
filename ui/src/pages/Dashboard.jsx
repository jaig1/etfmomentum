import { useState, useEffect } from 'react'
import { dashboardAPI } from '../services/api'
import './Dashboard.css'

function Dashboard() {
  const [universe, setUniverse] = useState('sp500')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [data, setData] = useState(null)

  useEffect(() => {
    fetchDashboard()
  }, [universe])

  const fetchDashboard = async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await dashboardAPI.getDashboard(universe)
      setData(result)
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

  if (loading) {
    return (
      <div className="container">
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading dashboard data...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container">
        <div className="alert alert-error">
          <strong>Error:</strong> {error}
        </div>
        <button className="btn btn-primary" onClick={fetchDashboard}>
          Retry
        </button>
      </div>
    )
  }

  return (
    <div className="container">
      <div className="page-header">
        <h1 className="page-title">Strategy Dashboard</h1>
        <p className="page-description">
          Current portfolio status and performance metrics
        </p>
      </div>

      {/* Universe Selector */}
      <div className="card">
        <div className="form-group">
          <label className="form-label">ETF Universe</label>
          <select
            className="form-select"
            value={universe}
            onChange={(e) => setUniverse(e.target.value)}
          >
            <option value="sp500">S&P 500 Sector ETFs (11 sectors)</option>
            <option value="developed">Developed Market ETFs</option>
            <option value="emerging">Emerging Market ETFs</option>
          </select>
        </div>
      </div>

      {/* Current Holdings */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Current Holdings</h2>
          <p className="card-subtitle">
            Top {data?.current_holdings?.length || 0} ETFs based on relative strength
          </p>
        </div>

        {data?.current_holdings && data.current_holdings.length > 0 ? (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Ticker</th>
                  <th>Name</th>
                  <th className="text-right">RS Ratio</th>
                  <th className="text-right">ROC %</th>
                  <th className="text-right">SMA Status</th>
                  <th className="text-right">Allocation</th>
                </tr>
              </thead>
              <tbody>
                {data.current_holdings.map((holding) => (
                  <tr key={holding.ticker}>
                    <td className="text-bold">{holding.ticker}</td>
                    <td>{holding.name}</td>
                    <td className="text-right">{formatNumber(holding.rs_ratio, 3)}</td>
                    <td className={`text-right ${getChangeClass(holding.roc_pct)}`}>
                      {formatPercent(holding.roc_pct)}
                    </td>
                    <td className="text-right">
                      <span className={`badge ${holding.sma_status ? 'badge-success' : 'badge-danger'}`}>
                        {holding.sma_status ? 'Above SMA' : 'Below SMA'}
                      </span>
                    </td>
                    <td className="text-right text-bold">
                      {formatPercent(holding.allocation, 1)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="alert alert-info">
            No holdings found for this universe. Try running signals generation.
          </div>
        )}
      </div>

      {/* Strategy Parameters */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Strategy Parameters</h2>
          <p className="card-subtitle">Current configuration</p>
        </div>

        {data?.parameters && (
          <div className="grid grid-4">
            <div className="stat-card">
              <div className="stat-label">Top N Holdings</div>
              <div className="stat-value">{data.parameters.top_n}</div>
            </div>

            <div className="stat-card">
              <div className="stat-label">SMA Lookback</div>
              <div className="stat-value">{data.parameters.sma_days}</div>
              <div className="text-muted" style={{ fontSize: '0.75rem', marginTop: '0.25rem' }}>
                days (~{Math.round(data.parameters.sma_days / 21)} months)
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-label">ROC Lookback</div>
              <div className="stat-value">{data.parameters.roc_days}</div>
              <div className="text-muted" style={{ fontSize: '0.75rem', marginTop: '0.25rem' }}>
                days (~{Math.round(data.parameters.roc_days / 21)} months)
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-label">Rebalance Frequency</div>
              <div className="stat-value" style={{ fontSize: '1.25rem' }}>
                {data.parameters.rebalance_freq}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Performance Summary */}
      {data?.performance && (
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Latest Performance</h2>
            <p className="card-subtitle">Most recent backtest results</p>
          </div>

          <div className="grid grid-3">
            <div className="stat-card">
              <div className="stat-label">Total Return</div>
              <div className={`stat-value ${getChangeClass(data.performance.total_return)}`}>
                {formatPercent(data.performance.total_return, 2)}
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-label">Sharpe Ratio</div>
              <div className="stat-value">
                {formatNumber(data.performance.sharpe_ratio, 3)}
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-label">Max Drawdown</div>
              <div className="stat-value text-danger">
                {formatPercent(data.performance.max_drawdown, 2)}
              </div>
            </div>
          </div>

          {data.performance.vs_spy !== null && (
            <div className="alert alert-info" style={{ marginTop: '1rem' }}>
              <strong>vs SPY:</strong> {formatPercent(data.performance.vs_spy, 2)} outperformance
            </div>
          )}
        </div>
      )}

      {/* ETF Universe Info */}
      {data?.universe_info && (
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">ETF Universe</h2>
            <p className="card-subtitle">{data.universe_info.count} ETFs available</p>
          </div>

          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Ticker</th>
                  <th>Name</th>
                  <th>Category</th>
                </tr>
              </thead>
              <tbody>
                {data.universe_info.etfs.map((etf) => (
                  <tr key={etf.ticker}>
                    <td className="text-bold">{etf.ticker}</td>
                    <td>{etf.name}</td>
                    <td>{etf.category || 'N/A'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Last Updated */}
      {data?.last_updated && (
        <div className="text-center text-muted" style={{ fontSize: '0.875rem', marginTop: '2rem' }}>
          Last updated: {new Date(data.last_updated).toLocaleString()}
        </div>
      )}
    </div>
  )
}

export default Dashboard
