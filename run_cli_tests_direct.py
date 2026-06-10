#!/usr/bin/env python3
"""Simple test runner for CLI tests"""
import sys
import os

sys.path.insert(0, '/app/label-studio/label_studio')
os.environ.setdefault('DJANGO_DB', 'sqlite')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.label_studio')

import django
django.setup()

from label_studio.core.argparser import parse_input_args

def run_test(name, test_fn):
    try:
        test_fn()
        print(f"✓ {name}")
        return True
    except Exception as e:
        print(f"✗ {name} FAILED: {e}")
        return False

def test_version_subcommand():
    args = parse_input_args(['version'])
    assert args.command == 'version', f"Expected 'version', got '{args.command}'"

def test_version_flag():
    args = parse_input_args(['--version'])
    assert args.version is True, f"Expected version=True, got {args.version}"

def test_version_with_additional_flags():
    args = parse_input_args(['version', '--debug'])
    assert args.command == 'version'
    assert args.debug is True

def test_start_subcommand():
    args = parse_input_args(['start'])
    assert args.command == 'start'

def test_start_with_project_name():
    args = parse_input_args(['start', 'my_project'])
    assert args.command == 'start'
    assert args.project_name == 'my_project'

def test_start_with_init_flag():
    args = parse_input_args(['start', '--init'])
    assert args.command == 'start'
    assert args.init is True

def test_start_with_project_and_init():
    args = parse_input_args(['start', 'my_project', '--init'])
    assert args.command == 'start'
    assert args.project_name == 'my_project'
    assert args.init is True

def test_empty_args():
    args = parse_input_args([])
    assert args.command is None

def test_only_flags_no_command():
    args = parse_input_args(['--debug'])
    assert args.command is None
    assert args.debug is True

def test_port_short_flag():
    args = parse_input_args(['start', '-p', '9000'])
    assert args.port == 9000, f"Expected port=9000, got {args.port}"

def test_port_long_flag():
    args = parse_input_args(['start', '--port', '8888'])
    assert args.port == 8888

def test_port_with_start_command():
    args = parse_input_args(['start', '--port', '3000'])
    assert args.command == 'start'
    assert args.port == 3000

def test_port_default_is_none():
    args = parse_input_args(['start'])
    assert args.port is None

def test_host_flag():
    args = parse_input_args(['start', '--host', 'http://example.com'])
    assert args.host == 'http://example.com'

def test_host_with_full_url():
    args = parse_input_args(['start', '--host', 'https://ls.domain.com/subdomain/'])
    assert args.host == 'https://ls.domain.com/subdomain/'

def test_host_default_is_empty_string():
    args = parse_input_args(['start'])
    assert args.host == ''

def test_data_dir_flag():
    args = parse_input_args(['start', '--data-dir', '/tmp/label-studio-data'])
    assert args.data_dir == '/tmp/label-studio-data'

def test_data_dir_with_start():
    args = parse_input_args(['start', '--data-dir', '/custom/path'])
    assert args.command == 'start'
    assert args.data_dir == '/custom/path'

def test_data_dir_default_is_none():
    args = parse_input_args(['start'])
    assert args.data_dir is None

def test_multiple_flags_together():
    args = parse_input_args([
        'start', 'my_project',
        '--port', '8080',
        '--host', 'http://localhost:8080',
        '--data-dir', '/tmp/data',
        '--debug',
    ])
    assert args.command == 'start'
    assert args.project_name == 'my_project'
    assert args.port == 8080
    assert args.host == 'http://localhost:8080'
    assert args.data_dir == '/tmp/data'
    assert args.debug is True

def test_port_as_string_raises():
    try:
        parse_input_args(['start', '--port', 'not_a_number'])
        assert False, "Should have raised SystemExit"
    except SystemExit:
        pass

def test_init_command():
    args = parse_input_args(['init', 'my_project'])
    assert args.command == 'init'
    assert args.project_name == 'my_project'

def test_init_quiet_mode():
    args = parse_input_args(['init', 'my_project', '--quiet'])
    assert args.command == 'init'
    assert args.quiet_mode is True

def test_user_command():
    args = parse_input_args(['user'])
    assert args.command == 'user'

def test_reset_password_command():
    args = parse_input_args(['reset_password'])
    assert args.command == 'reset_password'

def test_shell_command():
    args = parse_input_args(['shell'])
    assert args.command == 'shell'

def test_debug_flag():
    args = parse_input_args(['start', '--debug'])
    assert args.debug is True

def test_no_browser_flag():
    args = parse_input_args(['start', '--no-browser'])
    assert args.no_browser is True

def test_sampling_type():
    args = parse_input_args(['start', '--sampling', 'uniform'])
    assert args.sampling == 'uniform'

def test_log_level_choices():
    for level in ['DEBUG', 'INFO', 'WARNING', 'ERROR']:
        args = parse_input_args(['start', '--log-level', level])
        assert args.log_level == level, f"Expected log_level={level}, got {args.log_level}"

if __name__ == '__main__':
    print("Running CLI entry point tests...\n")
    
    tests = [
        ("test_version_subcommand", test_version_subcommand),
        ("test_version_flag", test_version_flag),
        ("test_version_with_additional_flags", test_version_with_additional_flags),
        ("test_start_subcommand", test_start_subcommand),
        ("test_start_with_project_name", test_start_with_project_name),
        ("test_start_with_init_flag", test_start_with_init_flag),
        ("test_start_with_project_and_init", test_start_with_project_and_init),
        ("test_empty_args", test_empty_args),
        ("test_only_flags_no_command", test_only_flags_no_command),
        ("test_port_short_flag", test_port_short_flag),
        ("test_port_long_flag", test_port_long_flag),
        ("test_port_with_start_command", test_port_with_start_command),
        ("test_port_default_is_none", test_port_default_is_none),
        ("test_host_flag", test_host_flag),
        ("test_host_with_full_url", test_host_with_full_url),
        ("test_host_default_is_empty_string", test_host_default_is_empty_string),
        ("test_data_dir_flag", test_data_dir_flag),
        ("test_data_dir_with_start", test_data_dir_with_start),
        ("test_data_dir_default_is_none", test_data_dir_default_is_none),
        ("test_multiple_flags_together", test_multiple_flags_together),
        ("test_port_as_string_raises", test_port_as_string_raises),
        ("test_init_command", test_init_command),
        ("test_init_quiet_mode", test_init_quiet_mode),
        ("test_user_command", test_user_command),
        ("test_reset_password_command", test_reset_password_command),
        ("test_shell_command", test_shell_command),
        ("test_debug_flag", test_debug_flag),
        ("test_no_browser_flag", test_no_browser_flag),
        ("test_sampling_type", test_sampling_type),
        ("test_log_level_choices", test_log_level_choices),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_fn in tests:
        if run_test(name, test_fn):
            passed += 1
        else:
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed, {passed + failed} total")
    
    if failed > 0:
        print("\nSome tests failed!")
        sys.exit(1)
    else:
        print("\nAll tests passed!")
        sys.exit(0)
