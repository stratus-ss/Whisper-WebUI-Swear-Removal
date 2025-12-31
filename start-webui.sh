#!/bin/bash

source venv/bin/activate

# Set up CUDA library paths to include cuDNN
CUDNN_PATH="$(pwd)/venv/lib/python3.11/site-packages/nvidia/cudnn/lib"
export LD_LIBRARY_PATH="${CUDNN_PATH}:${LD_LIBRARY_PATH}"

# Suppress cuDNN debug logging
export CUDNN_LOGINFO_DBG=0
export CUDNN_LOGDEST_DBG=stderr

python app.py "$@"

echo "launching the app"
