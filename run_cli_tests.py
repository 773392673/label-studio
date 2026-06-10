"""Ad-hoc runner for tests/test_cli.py - bypasses broken sandbox terminal."""
import os
import sys

os.chdir(os.path.join(os.path.dirname(__file__), 'label_studio'))
sys.path.insert(0, os.getcwd())

import pytest

sys.exit(pytest.main(['tests/test_cli.py', '-v', '--no-header', '-p', 'no:warnings']))
