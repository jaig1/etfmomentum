# ETF Momentum Strategy - API Backend

FastAPI backend that exposes the ETF momentum strategy as REST API endpoints.

## Installation

```bash
cd api
pip install -r requirements.txt
```

Or with uv:
```bash
cd api
uv pip install -r requirements.txt
```

## Running the API

### Development mode (with auto-reload):
```bash
cd api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Or:
```bash
python main.py
```

### Production mode:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Documentation

Once the server is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Health Check
- `GET /health` - Health check endpoint

### Dashboard
- `GET /api/dashboard?universe=sp500` - Get dashboard data including portfolio overview, current holdings, and YTD summary

### Signals
- `POST /api/signals` - Generate current portfolio signals with rebalancing recommendations
  ```json
  {
    "universe": "sp500"
  }
  ```
  Supported universes: `sp500`, `emerging`, `developed`. Parameters (SMA, ROC, Top N) are resolved automatically per universe — callers do not need to specify them.

### Backtest
- `POST /api/backtest` - Run historical backtest
  ```json
  {
    "universe": "sp500",
    "start_date": "2026-01-01",
    "end_date": "2026-03-15",
    "initial_capital": 100000,
    "top_n": 3,
    "rebalance_frequency": "weekly",
    "enable_volatility_regime": true,
    "refresh_data": true
  }
  ```

### Configuration
- `GET /api/config` - Get current strategy configuration
- `GET /api/universes` - Get list of available ETF universes

## CORS Configuration

The API is configured to accept requests from:
- `http://localhost:3000` (React default)
- `http://localhost:5173` (Vite default)

To add more origins, edit `main.py`:
```python
allow_origins=["http://localhost:3000", "http://your-domain.com"]
```

## Testing the API

### Using curl:
```bash
# Health check
curl http://localhost:8000/health

# Get dashboard
curl http://localhost:8000/api/dashboard?universe=sp500

# Generate signals
curl -X POST http://localhost:8000/api/signals \
  -H "Content-Type: application/json" \
  -d '{"universe": "sp500"}'

# Run backtest
curl -X POST http://localhost:8000/api/backtest \
  -H "Content-Type: application/json" \
  -d '{
    "universe": "sp500",
    "start_date": "2026-01-01",
    "end_date": "2026-03-15",
    "initial_capital": 100000,
    "top_n": 3,
    "rebalance_frequency": "weekly",
    "enable_volatility_regime": true,
    "refresh_data": true
  }'
```

### Using Python requests:
```python
import requests

# Get dashboard
response = requests.get("http://localhost:8000/api/dashboard?universe=sp500")
print(response.json())

# Generate signals
response = requests.post(
    "http://localhost:8000/api/signals",
    json={"universe": "sp500"}
)
print(response.json())
```

## Project Structure

```
api/
├── main.py              # FastAPI app entry point
├── routes/              # API route handlers
│   ├── dashboard.py    # Dashboard endpoints
│   ├── signals.py      # Signal generation endpoints
│   ├── backtest.py     # Backtest endpoints
│   └── config.py       # Configuration endpoints
├── models/              # Pydantic schemas
│   └── schemas.py      # Request/response models
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Environment Variables

The API uses the same `.env` file as the main application:
```
FMP_API_KEY=your_api_key_here
```

## Notes

- The API wraps the existing `etfmomentum` package without modifying it
- All business logic remains in the core Python modules
- The API layer only handles HTTP requests/responses and validation
- Data caching is handled by the existing data_fetcher module
