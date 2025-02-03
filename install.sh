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

# Install the package (pip will handle putting the script in the right place)
python3 -m pip install .

echo "✨ Installation complete! You can now use 'skyline' from any directory."
echo "Try 'skyline create --help' to get started."

# Cleanup
cd
rm -rf $TMP_DIR
