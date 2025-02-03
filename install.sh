#!/bin/bash

# Exit on error
set -e

echo "Installing Skyline..."

# Create temporary directory
TMP_DIR=$(mktemp -d)
cd $TMP_DIR

# Clone the repository
git clone https://github.com/cased/skyline.git
cd skyline

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install the package
pip install -e .

# Create symlink to make it globally available
INSTALL_PATH="/usr/local/bin/skyline"
sudo ln -sf "$(pwd)/venv/bin/skyline" "$INSTALL_PATH"

echo "✨ Installation complete! You can now use 'skyline' from any directory."
echo "Try 'skyline create --help' to get started."

# Cleanup
cd
rm -rf $TMP_DIR
