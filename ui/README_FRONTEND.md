# ETF Momentum Strategy - React Frontend

## Overview

This is the React frontend for the ETF Momentum Strategy application, built with Vite, React 18, React Router, and Axios.

## File Structure

```
src/
├── main.jsx                    # React entry point with BrowserRouter
├── index.css                   # Global styles and utility classes
├── App.jsx                     # Main app component with routing
├── App.css                     # App-level styles
│
├── services/
│   └── api.js                  # API client with axios
│
├── components/
│   ├── Navigation.jsx          # Navigation bar component
│   └── Navigation.css          # Navigation styles
│
└── pages/
    ├── Dashboard.jsx           # Dashboard page (Screen 1)
    ├── Dashboard.css
    ├── Signals.jsx             # Signal generation page (Screen 2)
    ├── Signals.css
    ├── Backtest.jsx            # Backtest page (Screen 3)
    └── Backtest.css
```

## Features Implemented

### 1. Dashboard Page (`/`)
- Universe selector (S&P 500 / Developed / Emerging markets)
- Current holdings display with RS ratios, ROC %, and SMA status
- Strategy parameters overview
- Latest performance metrics (Total Return, Sharpe Ratio, Max Drawdown)
- Complete ETF universe listing
- Auto-refreshes when universe changes

### 2. Signals Page (`/signals`)
- Configuration form:
  - Universe selector
  - Detailed mode toggle (show all ETF status)
  - Refresh data toggle (fetch latest prices)
- Top holdings display (BUY signals) with rankings
- All ETF status table (when detailed mode enabled)
- Parameters display (Top N, SMA lookback, ROC lookback)
- Real-time signal generation

### 3. Backtest Page (`/backtest`)
- Configuration form:
  - Universe selector
  - Date range picker (start/end dates)
  - Refresh data toggle
- Performance summary (4 key metrics)
- Benchmark comparison (Strategy vs SPY)
- Yearly returns breakdown
- Sample portfolio allocations (last 6 periods)
- Parameters display

## API Integration

All API calls use the axios client in `src/services/api.js`:

### Endpoints Used:
- **GET /api/dashboard?universe={universe}** - Dashboard data
- **POST /api/signals** - Generate signals
- **POST /api/backtest** - Run backtest

### API Configuration:
- Base URL: `http://localhost:8000` (default)
- Override via environment variable: `VITE_API_BASE_URL`
- Timeout: 120 seconds (for long-running backtests)
- Automatic error handling and retry logic

## Styling

### Design System:
- **Colors:**
  - Primary: #2563eb (blue)
  - Success: #16a34a (green)
  - Danger: #dc2626 (red)
  - Warning: #f59e0b (amber)
  
- **Typography:**
  - System fonts (Apple, Segoe UI, Roboto)
  - 0.875rem base font size for tables/forms
  - Bold headings with proper hierarchy

- **Components:**
  - Card-based layout with shadows
  - Responsive grid system (2/3/4 columns)
  - Badge system for status indicators
  - Loading spinners and error alerts
  - Clean table design with hover states

### Responsive Design:
- Desktop-first approach
- Breakpoints:
  - 1024px: 4-column grid becomes 2-column
  - 768px: All grids become single column
  - Navigation collapses to stacked layout on mobile

## Running the Application

### Install Dependencies:
```bash
npm install
# or
yarn install
```

### Development Server:
```bash
npm run dev
# Runs on http://localhost:5173
```

### Build for Production:
```bash
npm run build
# Output: dist/
```

### Preview Production Build:
```bash
npm run preview
```

## Environment Variables

Create a `.env` file in the project root:

```env
VITE_API_BASE_URL=http://localhost:8000
```

## Key Features

### User Experience:
- Clean, professional interface
- Loading states with spinners
- Error handling with user-friendly messages
- Success/info/warning/error alerts
- Responsive tables with horizontal scroll
- Hover effects and transitions
- Color-coded values (green for positive, red for negative)

### Data Display:
- Number formatting (2-3 decimal places)
- Percentage formatting with % symbol
- Currency formatting with $ symbol
- Badge system for status (Above/Below SMA, Pass/Fail)
- Ranking system for signals
- Comparison cards (Strategy vs Benchmark)

### Navigation:
- Sticky header
- Active route highlighting
- Three main sections clearly labeled
- Brand identity with title and subtitle

## Integration with Backend

This frontend expects the FastAPI backend to be running on port 8000 with the following endpoints:

1. `/api/dashboard` - Returns current holdings, parameters, performance
2. `/api/signals` - Generates signals for selected universe
3. `/api/backtest` - Runs historical backtest with date range

Make sure the backend is running before starting the frontend development server.

## Browser Support

- Modern browsers (Chrome, Firefox, Safari, Edge)
- ES6+ JavaScript required
- CSS Grid and Flexbox support required

## Notes

- All API calls include proper error handling
- Loading states prevent multiple concurrent requests
- Form validation happens on submit
- Data is formatted consistently across all pages
- Responsive design works on desktop, tablet, and mobile
