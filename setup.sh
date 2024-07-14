#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

VENV_DIR="venv"
REQUIREMENTS_FILE="requirements.txt"

python3 -m venv $VENV_DIR
source $VENV_DIR/bin/activate
echo "prompt-toolkit" > $REQUIREMENTS_FILE

pip install --upgrade pip
pip install -r $REQUIREMENTS_FILE

echo "Setup completed successfully!"