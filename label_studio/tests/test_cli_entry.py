"""This file and its contents are licensed under the Apache License 2.0. Please see the included NOTICE for copyright information and LICENSE for a copy of the license."""

import os
import sys
from unittest.mock import patch, MagicMock, call

import pytest

from label_studio.core.argparser import parse_input_args


class TestParseInputArgsVersion:
    def test_version_subcommand(self):
        args = parse_input_args(['version'])
        assert args.command == 'version'

    def test_version_flag(self):
        args = parse_input_args(['--version'])
        assert args.version is True

    def test_version_with_additional_flags(self):
        args = parse_input_args(['version', '--debug'])
        assert args.command == 'version'
        assert args.debug is True


class TestParseInputArgsStart:
    def test_start_subcommand(self):
        args = parse_input_args(['start'])
        assert args.command == 'start'

    def test_start_with_project_name(self):
        args = parse_input_args(['start', 'my_project'])
        assert args.command == 'start'
        assert args.project_name == 'my_project'

    def test_start_with_init_flag(self):
        args = parse_input_args(['start', '--init'])
        assert args.command == 'start'
        assert args.init is True

    def test_start_with_project_and_init(self):
        args = parse_input_args(['start', 'my_project', '--init'])
        assert args.command == 'start'
        assert args.project_name == 'my_project'
        assert args.init is True


class TestParseInputArgsNoCommand:
    def test_empty_args(self):
        args = parse_input_args([])
        assert args.command is None

    def test_only_flags_no_command(self):
        args = parse_input_args(['--debug'])
        assert args.command is None
        assert args.debug is True


class TestParseInputArgsPort:
    def test_port_short_flag(self):
        args = parse_input_args(['start', '-p', '9000'])
        assert args.port == 9000

    def test_port_long_flag(self):
        args = parse_input_args(['start', '--port', '8888'])
        assert args.port == 8888

    def test_port_with_start_command(self):
        args = parse_input_args(['start', '--port', '3000'])
        assert args.command == 'start'
        assert args.port == 3000

    def test_port_default_is_none(self):
        args = parse_input_args(['start'])
        assert args.port is None


class TestParseInputArgsHost:
    def test_host_flag(self):
        args = parse_input_args(['start', '--host', 'http://example.com'])
        assert args.host == 'http://example.com'

    def test_host_with_full_url(self):
        args = parse_input_args(['start', '--host', 'https://ls.domain.com/subdomain/'])
        assert args.host == 'https://ls.domain.com/subdomain/'

    def test_host_default_is_empty_string(self):
        args = parse_input_args(['start'])
        assert args.host == ''


class TestParseInputArgsDataDir:
    def test_data_dir_flag(self):
        args = parse_input_args(['start', '--data-dir', '/tmp/label-studio-data'])
        assert args.data_dir == '/tmp/label-studio-data'

    def test_data_dir_with_start(self):
        args = parse_input_args(['start', '--data-dir', '/custom/path'])
        assert args.command == 'start'
        assert args.data_dir == '/custom/path'

    def test_data_dir_default_is_none(self):
        args = parse_input_args(['start'])
        assert args.data_dir is None


class TestParseInputArgsCombined:
    def test_multiple_flags_together(self):
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


class TestMainVersionCommand:
    @pytest.mark.django_db
    def test_version_command_prints_version(self, mocker):
        from label_studio.server import main

        mocker.patch('sys.argv', ['label-studio', 'version'])
        mocker.patch('label_studio.server._setup_env')
        mocker.patch('label_studio.server._apply_database_migrations')
        mocker.patch('label_studio.server.collect_versions', return_value={'version': '1.0.0'})
        mocker.patch('label_studio.__version__', '1.0.0')

        with patch('builtins.print') as mock_print:
            main()
            mock_print.assert_any_call('\nLabel Studio version:', '1.0.0', '\n')


class TestMainStartCommand:
    @pytest.mark.django_db
    def test_start_command_sets_port_from_args(self, mocker):
        from label_studio.server import main

        mocker.patch('sys.argv', ['label-studio', 'start', '--port', '9090'])
        mocker.patch('label_studio.server._setup_env')
        mocker.patch('label_studio.server._apply_database_migrations')
        mocker.patch('label_studio.server.collect_versions', return_value={})
        mocker.patch('label_studio.server._get_config', return_value={})
        mocker.patch('label_studio.server._get_free_port', return_value=9090)
        mocker.patch('label_studio.server.start_browser')
        mocker.patch('label_studio.server._app_run')
        mocker.patch('label_studio.server.get_env', return_value=None)

        mock_settings = MagicMock()
        mocker.patch('django.conf.settings', mock_settings)

        main()

        assert mock_settings.INTERNAL_PORT == '9090'

    @pytest.mark.django_db
    def test_start_command_sets_host_from_args(self, mocker):
        from label_studio.server import main

        mocker.patch('sys.argv', ['label-studio', 'start', '--host', 'http://custom.host:8080'])
        mocker.patch('label_studio.server._setup_env')
        mocker.patch('label_studio.server._apply_database_migrations')
        mocker.patch('label_studio.server.collect_versions', return_value={})
        mocker.patch('label_studio.server._get_config', return_value={})
        mocker.patch('label_studio.server._get_free_port', return_value=8080)
        mocker.patch('label_studio.server.start_browser')
        mocker.patch('label_studio.server._app_run')

        mock_os_environ = {}
        mocker.patch.dict(os.environ, {}, clear=True)
        mocker.patch('label_studio.server.get_env', side_effect=lambda k: mock_os_environ.get(k))

        def mock_setdefault(key, value):
            mock_os_environ[key] = value

        mocker.patch('os.environ.setdefault', side_effect=mock_setdefault)

        main()

        assert mock_os_environ.get('HOST') == 'http://custom.host:8080'

    @pytest.mark.django_db
    def test_start_command_sets_data_dir_env(self, mocker):
        from label_studio.server import main

        mocker.patch('sys.argv', ['label-studio', 'start', '--data-dir', '/tmp/test-data'])
        mocker.patch('label_studio.server._setup_env')
        mocker.patch('label_studio.server._apply_database_migrations')
        mocker.patch('label_studio.server.collect_versions', return_value={})
        mocker.patch('label_studio.server._get_config', return_value={})
        mocker.patch('label_studio.server._get_free_port', return_value=8080)
        mocker.patch('label_studio.server.start_browser')
        mocker.patch('label_studio.server._app_run')
        mocker.patch('label_studio.server.get_env', return_value=None)

        mock_settings = MagicMock()
        mocker.patch('django.conf.settings', mock_settings)

        with patch.dict(os.environ, {}, clear=True):
            main()
            assert 'LABEL_STUDIO_BASE_DATA_DIR' in os.environ
            assert os.environ['LABEL_STUDIO_BASE_DATA_DIR'].endswith('test-data')

    @pytest.mark.django_db
    def test_start_command_calls_app_run_with_correct_params(self, mocker):
        from label_studio.server import main

        mocker.patch('sys.argv', ['label-studio', 'start', '--port', '7070', '--internal-host', '127.0.0.1'])
        mocker.patch('label_studio.server._setup_env')
        mocker.patch('label_studio.server._apply_database_migrations')
        mocker.patch('label_studio.server.collect_versions', return_value={})
        mocker.patch('label_studio.server._get_config', return_value={'internal_host': '0.0.0.0'})
        mocker.patch('label_studio.server._get_free_port', return_value=7070)
        mocker.patch('label_studio.server.start_browser')
        mock_app_run = mocker.patch('label_studio.server._app_run')
        mocker.patch('label_studio.server.get_env', return_value=None)

        mock_settings = MagicMock()
        mocker.patch('django.conf.settings', mock_settings)

        main()

        mock_app_run.assert_called_once_with(host='127.0.0.1', port=7070)

    @pytest.mark.django_db
    def test_start_without_port_uses_default(self, mocker):
        from label_studio.server import main

        mocker.patch('sys.argv', ['label-studio', 'start'])
        mocker.patch('label_studio.server._setup_env')
        mocker.patch('label_studio.server._apply_database_migrations')
        mocker.patch('label_studio.server.collect_versions', return_value={})
        mocker.patch('label_studio.server._get_config', return_value={})
        mocker.patch('label_studio.server._get_free_port', return_value=8080)
        mocker.patch('label_studio.server.start_browser')
        mocker.patch('label_studio.server._app_run')
        mocker.patch('label_studio.server.get_env', return_value=None)

        mock_settings = MagicMock()
        mocker.patch('django.conf.settings', mock_settings)

        main()

        assert mock_settings.INTERNAL_PORT == '8080'


class TestMainNoCommand:
    @pytest.mark.django_db
    def test_no_command_behaves_like_start(self, mocker):
        from label_studio.server import main

        mocker.patch('sys.argv', ['label-studio'])
        mocker.patch('label_studio.server._setup_env')
        mocker.patch('label_studio.server._apply_database_migrations')
        mocker.patch('label_studio.server.collect_versions', return_value={})
        mocker.patch('label_studio.server._get_config', return_value={})
        mocker.patch('label_studio.server._get_free_port', return_value=8080)
        mocker.patch('label_studio.server.start_browser')
        mocker.patch('label_studio.server._app_run')
        mocker.patch('label_studio.server.get_env', return_value=None)

        mock_settings = MagicMock()
        mocker.patch('django.conf.settings', mock_settings)

        main()

        mock_settings.INTERNAL_PORT = '8080'

    @pytest.mark.django_db
    def test_no_command_with_port_flag(self, mocker):
        from label_studio.server import main

        mocker.patch('sys.argv', ['label-studio', '--port', '9999'])
        mocker.patch('label_studio.server._setup_env')
        mocker.patch('label_studio.server._apply_database_migrations')
        mocker.patch('label_studio.server.collect_versions', return_value={})
        mocker.patch('label_studio.server._get_config', return_value={})
        mocker.patch('label_studio.server._get_free_port', return_value=9999)
        mocker.patch('label_studio.server.start_browser')
        mocker.patch('label_studio.server._app_run')
        mocker.patch('label_studio.server.get_env', return_value=None)

        mock_settings = MagicMock()
        mocker.patch('django.conf.settings', mock_settings)

        main()

        assert mock_settings.INTERNAL_PORT == '9999'


class TestMainEnvironmentVariables:
    @pytest.mark.django_db
    def test_database_sets_env(self, mocker):
        from label_studio.server import main

        mocker.patch('sys.argv', ['label-studio', 'start', '--database', '/tmp/test.db'])
        mocker.patch('label_studio.server._setup_env')
        mocker.patch('label_studio.server._apply_database_migrations')
        mocker.patch('label_studio.server.collect_versions', return_value={})
        mocker.patch('label_studio.server._get_config', return_value={})
        mocker.patch('label_studio.server._get_free_port', return_value=8080)
        mocker.patch('label_studio.server.start_browser')
        mocker.patch('label_studio.server._app_run')
        mocker.patch('label_studio.server.get_env', return_value=None)

        mock_settings = MagicMock()
        mocker.patch('django.conf.settings', mock_settings)

        with patch.dict(os.environ, {}, clear=True):
            main()
            assert 'DATABASE_NAME' in os.environ
            assert os.environ['DATABASE_NAME'].endswith('test.db')

    @pytest.mark.django_db
    def test_log_level_sets_env(self, mocker):
        from label_studio.server import main

        mocker.patch('sys.argv', ['label-studio', 'start', '--log-level', 'DEBUG'])
        mocker.patch('label_studio.server._setup_env')
        mocker.patch('label_studio.server._apply_database_migrations')
        mocker.patch('label_studio.server.collect_versions', return_value={})
        mocker.patch('label_studio.server._get_config', return_value={})
        mocker.patch('label_studio.server._get_free_port', return_value=8080)
        mocker.patch('label_studio.server.start_browser')
        mocker.patch('label_studio.server._app_run')
        mocker.patch('label_studio.server.get_env', return_value=None)

        mock_settings = MagicMock()
        mocker.patch('django.conf.settings', mock_settings)

        with patch.dict(os.environ, {}, clear=True):
            main()
            assert os.environ.get('LOG_LEVEL') == 'DEBUG'


class TestArgParserEdgeCases:
    def test_port_as_string_raises(self):
        with pytest.raises(SystemExit):
            parse_input_args(['start', '--port', 'not_a_number'])

    def test_init_command(self):
        args = parse_input_args(['init', 'my_project'])
        assert args.command == 'init'
        assert args.project_name == 'my_project'

    def test_init_quiet_mode(self):
        args = parse_input_args(['init', 'my_project', '--quiet'])
        assert args.command == 'init'
        assert args.quiet_mode is True

    def test_user_command(self):
        args = parse_input_args(['user'])
        assert args.command == 'user'

    def test_reset_password_command(self):
        args = parse_input_args(['reset_password'])
        assert args.command == 'reset_password'

    def test_shell_command(self):
        args = parse_input_args(['shell'])
        assert args.command == 'shell'

    def test_debug_flag(self):
        args = parse_input_args(['start', '--debug'])
        assert args.debug is True

    def test_no_browser_flag(self):
        args = parse_input_args(['start', '--no-browser'])
        assert args.no_browser is True

    def test_sampling_type(self):
        args = parse_input_args(['start', '--sampling', 'uniform'])
        assert args.sampling == 'uniform'

    def test_log_level_choices(self):
        for level in ['DEBUG', 'INFO', 'WARNING', 'ERROR']:
            args = parse_input_args(['start', '--log-level', level])
            assert args.log_level == level
