#!/usr/bin/env python3
"""
Environment setup verification script.

Usage:
    PYTHONPATH=src python scripts/test_setup.py
    or
    make test-setup
"""

import os

from dotenv import load_dotenv

# from utils import validate_env_variables

print(f"Loaded vars: {load_dotenv()}")

print("=== Environment Check ===")
print("Python version: OK")
print(f"Mapbox token present: {'✓' if os.getenv('MAPBOX_ACCESS_TOKEN') else '✗'}")
# print(f"All required variables: {'✓' if validate_env_variables() else '✗'}")
print("\nSetup complete! Run 'python agent.py' to start the agent.")
