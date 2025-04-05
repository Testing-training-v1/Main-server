# CircleCI Integration Guide

This document explains how to set up and use CircleCI with the Backdoor AI Learning Server. The server has been optimized to run in a memory-only mode on CircleCI, just like on Render, to efficiently utilize resources and avoid filesystem access issues.

## 1. Configuration Files

The CircleCI configuration is defined in the following files:
- `.circleci/config.yml` - Main CircleCI configuration
- `circleci_entrypoint.sh` - CircleCI-specific entry point script
- Memory-only mode optimizations in the codebase

## 2. Required Environment Variables

You must set the following environment variables in your CircleCI project settings:

| Variable Name | Description | Required |
|---------------|-------------|----------|
| `DROPBOX_REFRESH_TOKEN` | The OAuth2 refresh token for Dropbox access | Yes |
| `DROPBOX_APP_KEY` | Your Dropbox App Key | No (default in config) |
| `DROPBOX_APP_SECRET` | Your Dropbox App Secret | No (default in config) |

### Setting Environment Variables in CircleCI

1. Go to your CircleCI project
2. Click on "Project Settings" (gear icon)
3. Select "Environment Variables" from the sidebar
4. Add each of the variables listed above

## 3. Memory-Only Mode

The application automatically detects the CircleCI environment and enables memory-only mode, which:

- Uses Dropbox for all storage needs
- Streams files directly from Dropbox without local caching
- Patches the tempfile module to use in-memory implementations
- Avoids all filesystem operations

This dramatically reduces memory usage and prevents issues with CircleCI's filesystem limitations.

## 4. CircleCI Workflows

The CircleCI configuration includes two main jobs:

1. **build-and-test**: Builds the application and runs tests in memory-only mode
2. **deploy**: Runs only on the main branch after successful tests (customize as needed)

## 5. Local Testing of CircleCI Configuration

You can test the CircleCI configuration locally using the CircleCI CLI:

```bash
# Install CircleCI CLI
curl -fLSs https://raw.githubusercontent.com/CircleCI/local-cli/master/install.sh | bash

# Validate the configuration
circleci config validate

# Run the build job locally
circleci local execute --job build-and-test
```

## 6. Troubleshooting

### Missing Dropbox Token

If you see errors like:
```
Warning: DROPBOX_REFRESH_TOKEN not set. Running with limited functionality.
```

Ensure you've set the `DROPBOX_REFRESH_TOKEN` environment variable in CircleCI.

### Memory Issues

If you encounter memory issues:

1. Update the resource_class in `.circleci/config.yml` to a larger size
2. Check for memory leaks in your code
3. Ensure the memory-only mode is properly enabled

## 7. Configuring Dropbox

Before running in CircleCI, ensure your Dropbox is properly set up:

1. Run the `dropbox_config_setup.py` script once to create all necessary folders
2. Verify the base model is uploaded to the base_model folder
3. Confirm the database schema is initialized

## 8. Custom CircleCI Environment

If you need to disable memory-only mode (not recommended):

1. Add `DISABLE_MEMORY_ONLY_MODE: "True"` to the environment section in `.circleci/config.yml`
2. Be aware this may cause issues with filesystem permissions and memory usage
