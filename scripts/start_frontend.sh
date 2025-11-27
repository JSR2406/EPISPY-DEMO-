#!/bin/bash
# Start Frontend Development Server

set -e

cd frontend

echo "Installing frontend dependencies..."
npm install

echo "Starting frontend development server..."
npm run dev

# For production build:
# npm run build
# npm run preview

