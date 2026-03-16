import { useState } from 'react'
import { signalsAPI } from '../services/api'
import './Signals.css'

function Signals() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [results, setResults] = useState(null)

  const [formData, setFormData] = useState({
    universe: 'sp500',
    detailed: true,
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
      const result = await signalsAPI.generateSignals(formData)
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
        <h1 className="page-title">Signal Generation</h1>
        <p className="page-description">
          Generate current ETF momentum signals based on latest market data
        </p>
      </div>

      {/* Configuration Form */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Configuration</h2>
          <p className="card-subtitle">Set parameters for signal generation</p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="grid grid-2">
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
              <label className="form-label">Options</label>
              <div className="checkbox-group">
                <div className="form-checkbox">
                  <input
                    type="checkbox"
                    id="detailed"
                    name="detailed"
                    checked={formData.detailed}
                    onChange={handleInputChange}
                    disabled={loading}
                  />
                  <label htmlFor="detailed">Show detailed status for all ETFs</label>
                </div>
                <div className="form-checkbox">
                  <input
                    type="checkbox"
                    id="refresh"
                    name="refresh"
                    checked={formData.refresh}
                    onChange={handleInputChange}
                    disabled={loading}
                  />
                  <label htmlFor="refresh">Refresh data from API (latest prices)</label>
                </div>
              </div>
            </div>
          </div>

          <div className="form-actions">
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
            >
              {loading ? 'Generating Signals...' : 'Generate Signals'}
            </button>
          </div>
        </form>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="card">
          <div className="loading-container">
            <div className="spinner"></div>
            <p>Generating signals... This may take a moment.</p>
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
            <strong>Success!</strong> Signals generated successfully for {results.universe} universe.
          </div>

          {/* Top Holdings (BUY Signals) */}
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Top Holdings - BUY Signals</h2>
              <p className="card-subtitle">
                {results.top_holdings?.length || 0} ETFs recommended for current month
              </p>
            </div>

            {results.top_holdings && results.top_holdings.length > 0 ? (
              <div className="table-container">
                <table>
                  <thead>
                    <tr>
                      <th>Rank</th>
                      <th>Ticker</th>
                      <th className="text-right">RS Ratio</th>
                      <th className="text-right">ROC %</th>
                      <th className="text-right">Price</th>
                      <th className="text-right">SMA ({results.parameters?.sma_days}d)</th>
                      <th className="text-right">Allocation</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.top_holdings.map((signal, index) => (
                      <tr key={signal.ticker} className="highlight-row">
                        <td className="text-bold">{index + 1}</td>
                        <td className="text-bold signal-ticker">{signal.ticker}</td>
                        <td className="text-right">{formatNumber(signal.rs_ratio, 3)}</td>
                        <td className={`text-right ${getChangeClass(signal.roc_pct)}`}>
                          {formatPercent(signal.roc_pct)}
                        </td>
                        <td className="text-right">${formatNumber(signal.price)}</td>
                        <td className="text-right">${formatNumber(signal.sma)}</td>
                        <td className="text-right text-bold">
                          {formatPercent(signal.allocation, 1)}
                        </td>
                        <td>
                          <span className="badge badge-success">BUY</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="alert alert-warning">
                No ETFs currently meet the buy criteria (positive RS ratio and above SMA).
              </div>
            )}
          </div>

          {/* All ETF Status (if detailed mode) */}
          {formData.detailed && results.all_etf_status && (
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">All ETF Status</h2>
                <p className="card-subtitle">
                  Complete status for all {results.all_etf_status.length} ETFs in universe
                </p>
              </div>

              <div className="table-container">
                <table>
                  <thead>
                    <tr>
                      <th>Ticker</th>
                      <th className="text-right">RS Ratio</th>
                      <th className="text-right">ROC %</th>
                      <th className="text-right">Price</th>
                      <th className="text-right">SMA</th>
                      <th className="text-right">Above SMA</th>
                      <th className="text-right">RS Filter</th>
                      <th className="text-right">Dual Filter</th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.all_etf_status.map((etf) => (
                      <tr key={etf.ticker}>
                        <td className="text-bold">{etf.ticker}</td>
                        <td className="text-right">{formatNumber(etf.rs_ratio, 3)}</td>
                        <td className={`text-right ${getChangeClass(etf.roc_pct)}`}>
                          {formatPercent(etf.roc_pct)}
                        </td>
                        <td className="text-right">${formatNumber(etf.price)}</td>
                        <td className="text-right">${formatNumber(etf.sma)}</td>
                        <td className="text-right">
                          <span className={`badge ${etf.above_sma ? 'badge-success' : 'badge-danger'}`}>
                            {etf.above_sma ? 'Yes' : 'No'}
                          </span>
                        </td>
                        <td className="text-right">
                          <span className={`badge ${etf.rs_filter_pass ? 'badge-success' : 'badge-danger'}`}>
                            {etf.rs_filter_pass ? 'Pass' : 'Fail'}
                          </span>
                        </td>
                        <td className="text-right">
                          <span className={`badge ${etf.dual_filter_pass ? 'badge-success' : 'badge-danger'}`}>
                            {etf.dual_filter_pass ? 'Pass' : 'Fail'}
                          </span>
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
              Generated: {new Date(results.timestamp).toLocaleString()}
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default Signals
