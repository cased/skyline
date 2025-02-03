#!/bin/bash

# Exit on error
set -e

echo "Setting up Skyline development environment..."

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install in editable mode
pip install -e .

# Create symlink to make it globally available during development
INSTALL_PATH="/usr/local/bin/skyline"
if [ -L "$INSTALL_PATH" ]; then
    echo "Removing existing skyline symlink..."
    sudo rm "$INSTALL_PATH"
fi

echo "Creating skyline symlink..."
sudo ln -sf "$(pwd)/.venv/bin/skyline" "$INSTALL_PATH"

echo "✨ Development setup complete!"
echo "The 'skyline' command is now available globally."
echo "Changes to the source code will be reflected immediately."
