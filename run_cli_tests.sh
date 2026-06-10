#!/usr/bin/env bash
cd /app/label-studio/label_studio
export DJANGO_DB=sqlite
export DJANGO_SETTINGS_MODULE=core.settings.label_studio
export PYTHONPATH=/app/label-studio/label_studio:$PYTHONPATH
/app/label-studio/.venv/bin/python -m pytest tests/test_cli_entry.py -v 2>&1
