import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000, // 2 minutes for long-running backtests
})

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Server responded with error status
      console.error('API Error:', error.response.data)
      throw new Error(error.response.data.detail || error.response.data.error || 'An error occurred')
    } else if (error.request) {
      // Request made but no response
      console.error('Network Error:', error.request)
      throw new Error('Network error. Please check your connection.')
    } else {
      // Something else happened
      console.error('Error:', error.message)
      throw new Error(error.message)
    }
  }
)

export const dashboardAPI = {
  // GET /api/dashboard?universe=sp500
  getDashboard: async (universe = 'sp500') => {
    const response = await api.get('/api/dashboard', {
      params: { universe }
    })
    return response.data
  }
}

export const signalsAPI = {
  // POST /api/signals
  generateSignals: async (params) => {
    const response = await api.post('/api/signals', params)
    return response.data
  }
}

export const backtestAPI = {
  // POST /api/backtest
  runBacktest: async (params) => {
    const response = await api.post('/api/backtest', params)
    return response.data
  }
}

export const healthAPI = {
  // GET /api/health
  checkHealth: async () => {
    const response = await api.get('/api/health')
    return response.data
  }
}

export default api
