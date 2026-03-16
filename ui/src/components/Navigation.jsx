import { NavLink } from 'react-router-dom'
import './Navigation.css'

function Navigation() {
  return (
    <nav className="navbar">
      <div className="container">
        <div className="navbar-content">
          <div className="navbar-brand">
            <h1 className="brand-title">ETF Momentum Strategy</h1>
            <p className="brand-subtitle">Dual Momentum Rotation System</p>
          </div>

          <div className="navbar-links">
            <NavLink
              to="/"
              className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}
              end
            >
              Dashboard
            </NavLink>
            <NavLink
              to="/signals"
              className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}
            >
              Signals
            </NavLink>
            <NavLink
              to="/backtest"
              className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}
            >
              Backtest
            </NavLink>
          </div>
        </div>
      </div>
    </nav>
  )
}

export default Navigation
