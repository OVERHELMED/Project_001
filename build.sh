#!/bin/bash
# Build script for Render deployment

echo "Setting Python version to 3.10..."
export PYTHON_VERSION=3.10.12

echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements-compatible.txt

echo "Build completed successfully!"
