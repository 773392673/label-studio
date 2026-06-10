import subprocess
import sys

result = subprocess.run(
    [sys.executable, '-m', 'pytest',
     '/app/label-studio/label_studio/tests/test_cli.py',
     '-v', '--no-header', '-p', 'no:warnings'],
    cwd='/app/label-studio/label_studio',
    capture_output=False,
)
sys.exit(result.returncode)
