#!/bin/bash

# Apex Retail Store Intelligence - Pipeline Executor
# Runs the simulated pipeline or YOLOv8 detector to feed events into the API.

echo "============================================="
echo "  Apex Retail Store Intelligence Pipeline"
echo "============================================="

# Detect directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Read arguments
MODE=${1:-"batch"}

# Check if Python is installed
if ! command -v python &> /dev/null
then
    echo "ERROR: python could not be found. Please install Python 3.8+."
    exit 1
fi

echo "Running event emitter in '${MODE}' mode..."
python "${DIR}/emit_simulated.py" --mode "${MODE}"

echo "============================================="
echo "Pipeline execution finished."
echo "============================================="
