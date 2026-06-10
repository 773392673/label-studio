#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, '/app/label-studio/label_studio')
os.environ.setdefault('DJANGO_DB', 'sqlite')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.label_studio')

import django
django.setup()

import pytest

sys.exit(pytest.main([
    '/app/label-studio/label_studio/tests/test_cli_entry.py',
    '-v',
    '--tb=short',
    '-p', 'no:warnings'
]))
