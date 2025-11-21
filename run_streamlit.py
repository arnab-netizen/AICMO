#!/usr/bin/env python
"""Wrapper to run Streamlit with PYTHONPATH set."""
import sys
import os
import subprocess

# Change to workspace dir
os.chdir("/workspaces/AICMO")

# Ensure /workspaces/AICMO is in the environment path
env = os.environ.copy()
env["PYTHONPATH"] = "/workspaces/AICMO:" + env.get("PYTHONPATH", "")

# Run streamlit as subprocess (non-blocking)
subprocess.Popen(
    [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "streamlit_pages/aicmo_operator.py",
        "--server.port",
        "8501",
        "--server.address",
        "0.0.0.0",
    ],
    env=env,
)
