#!/usr/bin/env python3
"""Run the security-txt-checker test suite."""

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent

if __name__ == "__main__":
    sys.path.insert(0, str(HERE))
    loader = unittest.TestLoader()
    suite = loader.discover(str(HERE), pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
