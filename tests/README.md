# Test Execution Guide

This directory contains tests for the CMDB project, including specific use case verifications (UC-04, UC-05, UC-06).

## Prerequisites

Ensure you are in the project root and have the virtual environment activated or accessible.

## Running Tests

You need to provide dummy environment variables for the Jira configuration to allow the application to start in test mode.

### Command
Run the following command from the project root:

```bash
export JIRA_USER_EMAIL=test@example.com
export JIRA_API_TOKEN=test_token
export JIRA_CLOUD_ID=test_cloud_id
export JIRA_ASSET_WORKSPACE_ID=test_workspace_id
export CMDB_HOST=localhost
export CMDB_PORT=8000
export CMDB_DEBUG=True

# Run all tests
./venv/bin/python -m pytest tests/

# Run specific use case tests
./venv/bin/python -m pytest tests/test_uc04_sync_health.py tests/test_uc05_discovery_target.py tests/test_uc06_attribute_mapping.py
```

## Test Files Description

- **test_uc04_sync_health.py**: Verifies UC-04 (Monitor Synchronization Health). Checks if the `/jobs` API endpoints return status and active job lists.
- **test_uc05_discovery_target.py**: Verifies UC-05 (Add Discovery Target). Checks if triggering the `/api/v1/auto` discovery endpoint successfully starts a background job.
- **test_uc06_attribute_mapping.py**: Verifies UC-06 (Configure Attribute Mapping). Checks the `JiraFieldMapper` service for loading, applying, and saving JSON configuration.
- **test_jira_client.py**: Unit tests for the Jira integration client.
- **integration/**: Contains integration tests for Linux sync and client connectivity.

