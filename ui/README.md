# ETF Momentum Strategy - React Frontend

React frontend for the ETF Momentum Strategy application.

## Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The app will be available at **http://localhost:3000**

## Prerequisites

- Node.js 18+ installed
- API backend running on port 8000

## Pages

### 1. Dashboard (`/`)
- Portfolio overview
- Current holdings
- YTD performance summary
- Volatility regime indicator

### 2. Signals (`/signals`)
- Generate current signals
- View recommended portfolio
- Rebalancing actions
- All ETF status (detailed mode)

### 3. Backtest (`/backtest`)
- Run historical backtests
- Configure parameters
- View performance results
- Yearly breakdown

## API Integration

The frontend connects to the FastAPI backend at:
- **Base URL:** `http://localhost:8000`
- **Proxy:** Configured in `vite.config.js` for `/api/*` routes

## Development

```bash
# Start dev server with hot reload
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Technology Stack

- **React 18** - UI framework
- **React Router** - Navigation
- **Axios** - HTTP client
- **Vite** - Build tool

## Project Structure

```
ui/
├── public/              # Static assets
├── src/
│   ├── components/     # Reusable components
│   │   └── Navigation.jsx
│   ├── pages/          # Page components
│   │   ├── Dashboard.jsx
│   │   ├── Signals.jsx
│   │   └── Backtest.jsx
│   ├── services/       # API client
│   │   └── api.js
│   ├── App.jsx         # Main app
│   ├── main.jsx        # Entry point
│   └── index.css       # Global styles
├── index.html
├── vite.config.js
└── package.json
```

## Troubleshooting

### API Connection Issues
If you see "Failed to fetch" errors:
1. Make sure the API backend is running: `./start_api.sh`
2. Check if port 8000 is accessible
3. Verify CORS settings in API backend

### Port Already in Use
If port 3000 is busy:
1. Kill the process: `lsof -ti:3000 | xargs kill -9`
2. Or change port in `vite.config.js`

### Dependencies Issues
```bash
rm -rf node_modules package-lock.json
npm install
```
