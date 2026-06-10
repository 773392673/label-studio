#!/usr/bin/env python3
"""Simple test runner for CLI tests without full pytest machinery"""
import sys
import os

sys.path.insert(0, '/app/label-studio/label_studio')
os.environ.setdefault('DJANGO_DB', 'sqlite')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.label_studio')

import django
django.setup()

from label_studio.core.argparser import parse_input_args

def test_version_subcommand():
    args = parse_input_args(['version'])
    assert args.command == 'version', f"Expected 'version', got '{args.command}'"
    print("✓ test_version_subcommand passed")

def test_version_flag():
    args = parse_input_args(['--version'])
    assert args.version is True, f"Expected version=True, got {args.version}"
    print("✓ test_version_flag passed")

def test_version_with_additional_flags():
    args = parse_input_args(['version', '--debug'])
    assert args.command == 'version'
    assert args.debug is True
    print("✓ test_version_with_additional_flags passed")

def test_start_subcommand():
    args = parse_input_args(['start'])
    assert args.command == 'start'
    print("✓ test_start_subcommand passed")

def test_start_with_project_name():
    args = parse_input_args(['start', 'my_project'])
    assert args.command == 'start'
    assert args.project_name == 'my_project'
    print("✓ test_start_with_project_name passed")

def test_start_with_init_flag():
    args = parse_input_args(['start', '--init'])
    assert args.command == 'start'
    assert args.init is True
    print("✓ test_start_with_init_flag passed")

def test_empty_args():
    args = parse_input_args([])
    assert args.command is None
    print("✓ test_empty_args passed")

def test_only_flags_no_command():
    args = parse_input_args(['--debug'])
    assert args.command is None
    assert args.debug is True
    print("✓ test_only_flags_no_command passed")

def test_port_short_flag():
    args = parse_input_args(['start', '-p', '9000'])
    assert args.port == 9000, f"Expected port=9000, got {args.port}"
    print("✓ test_port_short_flag passed")

def test_port_long_flag():
    args = parse_input_args(['start', '--port', '8888'])
    assert args.port == 8888
    print("✓ test_port_long_flag passed")

def test_port_with_start_command():
    args = parse_input_args(['start', '--port', '3000'])
    assert args.command == 'start'
    assert args.port == 3000
    print("✓ test_port_with_start_command passed")

def test_port_default_is_none():
    args = parse_input_args(['start'])
    assert args.port is None
    print("✓ test_port_default_is_none passed")

def test_host_flag():
    args = parse_input_args(['start', '--host', 'http://example.com'])
    assert args.host == 'http://example.com'
    print("✓ test_host_flag passed")

def test_host_with_full_url():
    args = parse_input_args(['start', '--host', 'https://ls.domain.com/subdomain/'])
    assert args.host == 'https://ls.domain.com/subdomain/'
    print("✓ test_host_with_full_url passed")

def test_host_default_is_empty_string():
    args = parse_input_args(['start'])
    assert args.host == ''
    print("✓ test_host_default_is_empty_string passed")

def test_data_dir_flag():
    args = parse_input_args(['start', '--data-dir', '/tmp/label-studio-data'])
    assert args.data_dir == '/tmp/label-studio-data'
    print("✓ test_data_dir_flag passed")

def test_data_dir_with_start():
    args = parse_input_args(['start', '--data-dir', '/custom/path'])
    assert args.command == 'start'
    assert args.data_dir == '/custom/path'
    print("✓ test_data_dir_with_start passed")

def test_data_dir_default_is_none():
    args = parse_input_args(['start'])
    assert args.data_dir is None
    print("✓ test_data_dir_default_is_none passed")

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
    print("✓ test_multiple_flags_together passed")

def test_port_as_string_raises():
    try:
        parse_input_args(['start', '--port', 'not_a_number'])
        assert False, "Should have raised SystemExit"
    except SystemExit:
        print("✓ test_port_as_string_raises passed")

def test_init_command():
    args = parse_input_args(['init', 'my_project'])
    assert args.command == 'init'
    assert args.project_name == 'my_project'
    print("✓ test_init_command passed")

def test_init_quiet_mode():
    args = parse_input_args(['init', 'my_project', '--quiet'])
    assert args.command == 'init'
    assert args.quiet_mode is True
    print("✓ test_init_quiet_mode passed")

def test_user_command():
    args = parse_input_args(['user'])
    assert args.command == 'user'
    print("✓ test_user_command passed")

def test_reset_password_command():
    args = parse_input_args(['reset_password'])
    assert args.command == 'reset_password'
    print("✓ test_reset_password_command passed")

def test_shell_command():
    args = parse_input_args(['shell'])
    assert args.command == 'shell'
    print("✓ test_shell_command passed")

def test_debug_flag():
    args = parse_input_args(['start', '--debug'])
    assert args.debug is True
    print("✓ test_debug_flag passed")

def test_no_browser_flag():
    args = parse_input_args(['start', '--no-browser'])
    assert args.no_browser is True
    print("✓ test_no_browser_flag passed")

def test_sampling_type():
    args = parse_input_args(['start', '--sampling', 'uniform'])
    assert args.sampling == 'uniform'
    print("✓ test_sampling_type passed")

def test_log_level_choices():
    for level in ['DEBUG', 'INFO', 'WARNING', 'ERROR']:
        args = parse_input_args(['start', '--log-level', level])
        assert args.log_level == level
    print("✓ test_log_level_choices passed")

if __name__ == '__main__':
    print("Running CLI entry point tests...\n")
    
    tests = [
        test_version_subcommand,
        test_version_flag,
        test_version_with_additional_flags,
        test_start_subcommand,
        test_start_with_project_name,
        test_start_with_init_flag,
        test_empty_args,
        test_only_flags_no_command,
        test_port_short_flag,
        test_port_long_flag,
        test_port_with_start_command,
        test_port_default_is_none,
        test_host_flag,
        test_host_with_full_url,
        test_host_default_is_empty_string,
        test_data_dir_flag,
        test_data_dir_with_start,
        test_data_dir_default_is_none,
        test_multiple_flags_together,
        test_port_as_string_raises,
        test_init_command,
        test_init_quiet_mode,
        test_user_command,
        test_reset_password_command,
        test_shell_command,
        test_debug_flag,
        test_no_browser_flag,
        test_sampling_type,
        test_log_level_choices,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed, {passed + failed} total")
    
    if failed > 0:
        sys.exit(1)
    else:
        print("\nAll tests passed!")
        sys.exit(0)
