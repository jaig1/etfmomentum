import { useState, useEffect } from 'react'
import { dashboardAPI } from '../services/api'
import './Dashboard.css'

// Helper function to get universe from URL on initial load
const getInitialUniverse = () => {
  const params = new URLSearchParams(window.location.search)
  const universeParam = params.get('universe')
  if (universeParam && ['sp500', 'emerging', 'developed'].includes(universeParam)) {
    console.log('📍 Initializing universe from URL:', universeParam)
    return universeParam
  }
  return 'sp500'
}

function Dashboard() {
  const [universe, setUniverse] = useState(getInitialUniverse)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [data, setData] = useState(null)

  // Fetch dashboard data
  const fetchDashboard = async () => {
    console.log('📊 Fetching dashboard data for:', universe)
    setLoading(true)
    setError(null)
    try {
      const result = await dashboardAPI.getDashboard(universe)
      console.log('✅ Dashboard data received:', result)
      setData(result)
      setLoading(false)
    } catch (err) {
      console.error('❌ Dashboard error:', err)
      setError(err.message)
      setLoading(false)
    }
  }

  // Debug logging
  useEffect(() => {
    console.log('🎨 Dashboard state:', { loading, hasData: !!data, hasError: !!error })
  }, [loading, data, error])

  useEffect(() => {
    fetchDashboard()
  }, [universe])

  const formatNumber = (num, decimals = 2) => {
    if (num === null || num === undefined) return 'N/A'
    return Number(num).toFixed(decimals)
  }

  const formatPercent = (num, decimals = 2) => {
    if (num === null || num === undefined) return 'N/A'
    const value = Number(num).toFixed(decimals)
    return `${value}%`
  }

  const formatCurrency = (num) => {
    if (num === null || num === undefined) return 'N/A'
    return `$${Number(num).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
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

  console.log('🎨 Rendering Dashboard with data')

  return (
    <div className="container">
      <div className="page-header">
        <h1 className="page-title">Strategy Dashboard</h1>
        <p className="page-description">
          YTD Backtest Simulation - Weekly Momentum Rebalancing vs SPY Buy & Hold
        </p>
      </div>

      {/* Simulation Info Banner */}
      <div className="alert alert-info" style={{ marginBottom: '1.5rem' }}>
        <strong>📊 Simulation Parameters:</strong> Starting from January 1, 2026 with $100,000 initial capital.
        The strategy rebalances weekly based on relative strength momentum signals (top 3 holdings, equal weight).
        Benchmark: $100,000 invested in SPY (buy and hold, no rebalancing).
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

      {/* YTD Performance Metrics */}
      {data && (
        <>
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">📈 YTD Backtest Results</h2>
              <p className="card-subtitle">
                Simulation Period: January 1, 2026 → {data.as_of_date} | Initial Investment: $100,000
              </p>
            </div>

            <div className="grid grid-3">
              <div className="metric-card">
                <div className="metric-label">Strategy Portfolio Value</div>
                <div className="metric-value">
                  {formatCurrency(data.portfolio_value)}
                </div>
                <div className={`metric-change ${getChangeClass(data.ytd_return)}`}>
                  {formatPercent(data.ytd_return)} YTD
                  {data.ytd_return !== 0 && (
                    <span style={{ fontSize: '0.875rem', marginLeft: '0.5rem' }}>
                      ({data.ytd_return > 0 ? '+' : ''}{formatCurrency(data.portfolio_value - 100000)})
                    </span>
                  )}
                </div>
              </div>

              <div className="metric-card">
                <div className="metric-label">SPY Benchmark Value</div>
                <div className="metric-value">
                  {formatCurrency(data.spy_value)}
                </div>
                <div className={`metric-change ${getChangeClass(data.spy_return)}`}>
                  {formatPercent(data.spy_return)} YTD
                  {data.spy_return !== 0 && (
                    <span style={{ fontSize: '0.875rem', marginLeft: '0.5rem' }}>
                      ({data.spy_return > 0 ? '+' : ''}{formatCurrency(data.spy_value - 100000)})
                    </span>
                  )}
                </div>
              </div>

              <div className="metric-card">
                <div className="metric-label">Strategy vs SPY</div>
                <div className={`metric-value ${getChangeClass(data.outperformance)}`}>
                  {formatPercent(data.outperformance, 2)}
                </div>
                <div className={`metric-change ${getChangeClass(data.portfolio_value - data.spy_value)}`}>
                  {data.portfolio_value > data.spy_value ? '+' : ''}{formatCurrency(data.portfolio_value - data.spy_value)} difference
                </div>
              </div>
            </div>

            <div className="grid grid-3" style={{ marginTop: '1rem' }}>
              <div className="metric-card">
                <div className="metric-label">Sharpe Ratio</div>
                <div className="metric-value">
                  {formatNumber(data.sharpe_ratio, 3)}
                </div>
              </div>

              <div className="metric-card">
                <div className="metric-label">Max Drawdown</div>
                <div className="metric-value negative">
                  {formatPercent(data.max_drawdown, 2)}
                </div>
              </div>

              <div className="metric-card">
                <div className="metric-label">Volatility Regime</div>
                <div className="metric-value" style={{ fontSize: '1rem' }}>
                  {data.volatility_regime?.replace('_', ' ')}
                </div>
              </div>
            </div>
          </div>

          {/* Current Holdings */}
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">💼 Current Portfolio Holdings</h2>
              <p className="card-subtitle">
                As of latest rebalance ({data.as_of_date}) - Top {data.current_holdings?.length || 0} ETFs ranked by relative strength momentum (equal weight: {data.current_holdings?.length > 0 ? formatPercent((1 / data.current_holdings.length) * 100, 1) : 'N/A'} each)
              </p>
            </div>

            {data.current_holdings && data.current_holdings.length > 0 ? (
              <div className="table-container">
                <table>
                  <thead>
                    <tr>
                      <th>Rank</th>
                      <th>Ticker</th>
                      <th>Name</th>
                      <th className="text-right">RS ROC</th>
                      <th className="text-right">Weight</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.current_holdings.map((holding, idx) => (
                      <tr key={holding.ticker || idx}>
                        <td className="text-bold">{holding.rank}</td>
                        <td className="text-bold" style={{ color: '#2563eb' }}>{holding.ticker}</td>
                        <td>{holding.name}</td>
                        <td className="text-right positive">
                          {formatPercent(holding.rs_roc * 100, 2)}
                        </td>
                        <td className="text-right text-bold">
                          {formatPercent(holding.weight * 100, 1)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="alert alert-info">
                No current holdings. Generate signals to see recommendations.
              </div>
            )}
          </div>

          {/* Monthly Performance Breakdown */}
          {data.ytd_summary && data.ytd_summary.length > 0 && (
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">📊 Monthly Performance Breakdown</h2>
                <p className="card-subtitle">
                  Monthly returns with weekly rebalancing - Strategy vs SPY Buy & Hold
                </p>
              </div>

              <div className="table-container">
                <table>
                  <thead>
                    <tr>
                      <th>Month</th>
                      <th className="text-right">Strategy Return</th>
                      <th className="text-right">SPY Return</th>
                      <th className="text-right">Outperformance</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.ytd_summary.map((month, idx) => (
                      <tr key={idx}>
                        <td className="text-bold">{month.month}</td>
                        <td className={`text-right ${getChangeClass(month.strategy_return)}`}>
                          {formatPercent(month.strategy_return, 2)}
                        </td>
                        <td className={`text-right ${getChangeClass(month.spy_return)}`}>
                          {formatPercent(month.spy_return, 2)}
                        </td>
                        <td className={`text-right ${getChangeClass(month.outperformance)}`}>
                          {formatPercent(month.outperformance, 2)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default Dashboard
