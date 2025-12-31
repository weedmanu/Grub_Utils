#!/bin/bash
# Script to remove all __pycache__ directories in the project

# Get the project root directory (assuming script is in script/ subdirectory)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Cleaning __pycache__ directories from $PROJECT_ROOT..."

find "$PROJECT_ROOT" -type d -name "__pycache__" -exec rm -rf {} +

echo "Done."
