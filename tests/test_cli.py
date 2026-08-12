"""Tests for the app.py CLI arguments.

Run in a subprocess: the server only starts on valid arguments, so argument
parsing is checked with invalid values and with --help.
"""
import os
import subprocess
import sys

import pytest

APP_SCRIPT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")


def run_app(*cli_args):
    return subprocess.run(
        [sys.executable, APP_SCRIPT, *cli_args],
        capture_output=True, text=True, timeout=60,
    )


@pytest.mark.parametrize("host", [
    "256.0.0.1",
    "1.2.3",
    "1.2.3.4.5",
    "example.com",
    "localhostt",
    "",
])
def test_invalid_host_is_rejected(host):
    result = run_app("--host", host)

    assert result.returncode == 2
    assert "invalid ipv4 or localhost value" in result.stderr


def test_invalid_port_is_rejected():
    result = run_app("--port", "not-a-port")

    assert result.returncode == 2
    assert "invalid int value" in result.stderr


def test_help_lists_arguments():
    result = run_app("--help")

    assert result.returncode == 0
    assert "--host" in result.stdout
    assert "--port" in result.stdout
