import sys
import os
import subprocess

sys.path.insert(0, os.path.dirname(__file__))

# Set auth env vars for tests if not already present
os.environ.setdefault("API_KEY", "test-api-key")
os.environ.setdefault("API_KEY_SYSTEM", "test-api-key-system")


def pytest_configure(config):
    if os.getenv("CHECK_DOCKER", "true").lower() != "true":
        return

    result = subprocess.run(["docker", "info"], capture_output=True)
    if result.returncode != 0:
        sys.exit("Docker is not running. Start Docker Desktop and try again.")