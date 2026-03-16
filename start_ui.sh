#!/bin/bash

# Start the ETF Momentum Strategy React UI

echo "Starting ETF Momentum Strategy React UI..."
echo "UI will be available at: http://localhost:3000"
echo ""
echo "Make sure the API backend is running on port 8000!"
echo "If not, run: ./start_api.sh in another terminal"
echo ""
echo "Press Ctrl+C to stop the UI server"
echo ""

cd "$(dirname "$0")/ui"
npm run dev
