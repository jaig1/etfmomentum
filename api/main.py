"""FastAPI backend for ETF Momentum Strategy UI."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import sys
from pathlib import Path

# Add parent directory to path to import etfmomentum package
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.routes import dashboard, signals, backtest, config


# Middleware to disable caching for all API responses
class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

app = FastAPI(
    title="ETF Momentum Strategy API",
    description="REST API for ETF Relative Strength Momentum Strategy",
    version="1.0.0"
)

# Add no-cache middleware (must be added before CORS)
app.add_middleware(NoCacheMiddleware)

# CORS middleware for React development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(dashboard.router, prefix="/api", tags=["Dashboard"])
app.include_router(signals.router, prefix="/api", tags=["Signals"])
app.include_router(backtest.router, prefix="/api", tags=["Backtest"])
app.include_router(config.router, prefix="/api", tags=["Config"])


@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "message": "ETF Momentum Strategy API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
