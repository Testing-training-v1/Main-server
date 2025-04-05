# Backdoor AI Learning Server - CircleCI Integration

## Quick Start

### 1. Setup CircleCI Project

1. **Connect your repository to CircleCI**:
   - Go to [CircleCI](https://circleci.com/)
   - Log in with your GitHub account
   - Add this repository as a project

2. **Set required environment variables**:
   - `DROPBOX_REFRESH_TOKEN`: Your Dropbox OAuth2 refresh token
   - Set these in Project Settings > Environment Variables

### 2. Configuration

The project includes:
- `.circleci/config.yml`: Main CircleCI configuration
- `circleci_entrypoint.sh`: Entry point script for CircleCI
- `circleci_tests/`: Directory with CircleCI-specific tests
- `CIRCLECI_SETUP.md`: Detailed setup instructions

### 3. Memory-Only Mode

This server uses memory-only mode on CircleCI, which:
- Streams models directly from Dropbox
- Uses no local filesystem for storage
- Implements virtual tempfile system for memory efficiency
- Automatically detects CircleCI environment

### 4. Testing Locally

Test the CircleCI setup locally:

```bash
# Install CircleCI CLI
curl -fLSs https://raw.githubusercontent.com/CircleCI/local-cli/master/install.sh | bash

# Validate config
circleci config validate

# Run locally
circleci local execute --job build-and-test
```

### 5. Run Tests Manually

You can run the CircleCI-specific tests manually:

```bash
# Set environment variables
export MEMORY_ONLY_MODE=True
export USE_DROPBOX_STREAMING=True
export NO_LOCAL_STORAGE=True
export CIRCLECI_ENV=True

# Run test script
python circleci_tests/test_memory_mode.py
```

## Detailed Documentation

For detailed setup instructions, see [CIRCLECI_SETUP.md](CIRCLECI_SETUP.md).
