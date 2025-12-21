import os

"""
Configuration file for pytest.
Sets up environment variables required by the application configuration
before any tests are collected or run. This prevents validation errors
when importing modules that instantiate settings.
"""

# Set environment variables before any tests are collected or run
os.environ["JIRA_USER_EMAIL"] = "test@example.com"
os.environ["JIRA_API_TOKEN"] = "test_token"
os.environ["JIRA_CLOUD_ID"] = "test_cloud_id"
os.environ["JIRA_ASSET_WORKSPACE_ID"] = "test_workspace_id"

