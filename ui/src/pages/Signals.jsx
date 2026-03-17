import { useState, useEffect } from 'react'
import { signalsAPI } from '../services/api'
import './Signals.css'

function Signals() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [data, setData] = useState(null)
  const [universe, setUniverse] = useState('sp500')

  // Debug logging for state changes
  useEffect(() => {
    console.log('State updated - loading:', loading, 'hasData:', !!data, 'hasError:', !!error)
  }, [loading, data, error])

  const handleGenerateSignals = async () => {
    console.log('🚀 Starting signal generation for:', universe)

    // Clear previous state
    setError(null)
    setData(null)
    setLoading(true)
    console.log('⏳ Loading state set to TRUE')

    try {
      const result = await signalsAPI.generateSignals({
        universe,
        top_n: 3
      })
      console.log('✅ API response received:', result)
      console.log('📊 Portfolio items:', result?.recommended_portfolio?.length)

      // Update state with results
      setData(result)
      console.log('💾 Data state updated')

      // Small delay to ensure data is set before clearing loading
      setTimeout(() => {
        setLoading(false)
        console.log('✅ Loading state set to FALSE')
      }, 0)

    } catch (err) {
      console.error('❌ Error generating signals:', err)
      setError(err.message || 'Failed to generate signals')
      setLoading(false)
      console.log('❌ Loading state set to FALSE (error)')
    }
  }

  const formatPercent = (num, decimals = 2) => {
    if (num === null || num === undefined) return 'N/A'
    return `${(num * 100).toFixed(decimals)}%`
  }

  console.log('🎨 Rendering Signals component - loading:', loading, 'hasData:', !!data)

  return (
    <div className="container">
      <div className="page-header">
        <h1 className="page-title">Signal Generation</h1>
        <p className="page-description">
          Generate current ETF momentum signals based on latest market data
        </p>
      </div>

      {/* Configuration */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Configuration</h2>
        </div>

        <div className="form-group">
          <label className="form-label">ETF Universe</label>
          <select
            className="form-select"
            value={universe}
            onChange={(e) => setUniverse(e.target.value)}
            disabled={loading}
          >
            <option value="sp500">S&P 500 Sector ETFs (11 sectors)</option>
            <option value="emerging">Emerging Market ETFs</option>
            <option value="developed">Developed Market ETFs</option>
          </select>
        </div>

        <div className="form-actions">
          <button
            onClick={handleGenerateSignals}
            className="btn btn-primary"
            disabled={loading}
          >
            {loading ? 'Generating Signals...' : 'Generate Signals'}
          </button>
        </div>
      </div>

      {/* Loading */}
      {loading && (
        <div className="card">
          <div className="loading-container">
            <div className="spinner"></div>
            <p>Generating signals... This may take a moment.</p>
          </div>
        </div>
      )}

      {/* Error */}
      {error && !loading && (
        <div className="alert alert-error">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Results */}
      {data && !loading && (() => {
        console.log('📊 Rendering results section - data exists and not loading')
        return (
          <>
            <div className="alert alert-success">
              <strong>Success!</strong> Generated signals for {data.universe} ({data.as_of_date})
            </div>

          {/* Recommended Portfolio */}
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">📊 Recommended Portfolio</h2>
              <p className="card-subtitle">
                Top {data.recommended_portfolio?.length || 0} ETFs for current allocation
              </p>
            </div>

            {data.recommended_portfolio && data.recommended_portfolio.length > 0 ? (
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
                    {data.recommended_portfolio.map((holding, idx) => {
                      try {
                        return (
                          <tr key={holding.ticker || idx}>
                            <td className="text-bold">{holding.rank}</td>
                            <td className="text-bold signal-ticker">{holding.ticker}</td>
                            <td>{holding.name}</td>
                            <td className="text-right positive">
                              {formatPercent(holding.rs_roc)}
                            </td>
                            <td className="text-right text-bold">
                              {formatPercent(holding.weight, 1)}
                            </td>
                          </tr>
                        )
                      } catch (err) {
                        console.error('Error rendering holding row:', err, holding)
                        return null
                      }
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <p>No portfolio recommendations available</p>
            )}
          </div>

          {/* Rebalancing Actions */}
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">🔄 Rebalancing Actions</h2>
              <p className="card-subtitle">{data.rebalancing_summary || 'No summary available'}</p>
            </div>

            {data.rebalancing_actions && data.rebalancing_actions.length > 0 ? (
              <div className="table-container">
                <table>
                  <thead>
                    <tr>
                      <th>Ticker</th>
                      <th className="text-right">Current</th>
                      <th className="text-right">Recommended</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.rebalancing_actions.map((action, idx) => {
                      try {
                        return (
                          <tr key={action.ticker || idx}>
                            <td className="text-bold signal-ticker">{action.ticker}</td>
                            <td className="text-right">{formatPercent(action.current_weight, 1)}</td>
                            <td className="text-right">{formatPercent(action.recommended_weight, 1)}</td>
                            <td>
                              <span className={`badge ${
                                action.action === 'BUY' ? 'badge-success' :
                                action.action === 'SELL' ? 'badge-danger' :
                                'badge-info'
                              }`}>
                                {action.action}
                              </span>
                            </td>
                          </tr>
                        )
                      } catch (err) {
                        console.error('Error rendering action row:', err, action)
                        return null
                      }
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <p>No rebalancing actions needed</p>
            )}
          </div>

          {/* All ETF Status */}
          {data.all_etf_status && data.all_etf_status.length > 0 && (
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">📈 All ETF Status</h2>
                <p className="card-subtitle">
                  Complete status for all {data.all_etf_status.length} ETFs in universe
                </p>
              </div>

              <div className="table-container">
                <table>
                  <thead>
                    <tr>
                      <th>Rank</th>
                      <th>Ticker</th>
                      <th className="text-right">Price</th>
                      <th className="text-right">RS ROC</th>
                      <th>RS Filter</th>
                      <th>Abs Filter</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.all_etf_status.map((etf, idx) => {
                      try {
                        return (
                          <tr key={etf.ticker || idx}>
                            <td>{etf.rank || '-'}</td>
                            <td className="text-bold">{etf.ticker}</td>
                            <td className="text-right">${etf.price?.toFixed(2) || 'N/A'}</td>
                            <td className="text-right">{formatPercent(etf.rs_roc)}</td>
                            <td>
                              <span className={`badge ${etf.rs_filter ? 'badge-success' : 'badge-danger'}`}>
                                {etf.rs_filter ? 'Pass' : 'Fail'}
                              </span>
                            </td>
                            <td>
                              <span className={`badge ${etf.abs_filter ? 'badge-success' : 'badge-danger'}`}>
                                {etf.abs_filter ? 'Pass' : 'Fail'}
                              </span>
                            </td>
                          </tr>
                        )
                      } catch (err) {
                        console.error('Error rendering ETF row:', err, etf)
                        return null
                      }
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
        )
      })()}
    </div>
  )
}

export default Signals
