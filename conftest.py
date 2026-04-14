import sys
import os
import subprocess

sys.path.insert(0, os.path.dirname(__file__))


def pytest_configure(config):
    if os.getenv("CHECK_DOCKER", "true").lower() != "true":
        return

    result = subprocess.run(["docker", "info"], capture_output=True)
    if result.returncode != 0:
        sys.exit("Docker is not running. Start Docker Desktop and try again.")