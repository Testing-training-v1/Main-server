#!/bin/bash
set -e

echo "Starting Backdoor AI Learning Server in CircleCI environment..."

# Set environment variables for CircleCI
export CIRCLECI_ENV="True"
export MEMORY_ONLY_MODE="True"
export NO_LOCAL_STORAGE="True"
export USE_DROPBOX_STREAMING="True"

# No directories needed in CircleCI - everything will stream from Dropbox
echo "Running in memory-only mode for CircleCI"

# Source the original entrypoint to reuse most of the startup logic
source ./entrypoint.sh

# This script is designed to be called from CircleCI config.yml
# The original entrypoint.sh will handle the rest of the startup process
