"""This file and its contents are licensed under the Apache License 2.0. Please see the included NOTICE for copyright information and LICENSE for a copy of the license."""

import os
import socket
from unittest.mock import MagicMock, patch

import pytest
from server import _create_user
from tests.utils import make_annotation, make_project, make_task

from label_studio.core.argparser import parse_input_args


@pytest.mark.django_db
def test_create_user():
    input_args = parse_input_args(['init', 'test', '--username', 'default@localhost', '--password', '12345678'])
    config = {}
    user = _create_user(input_args, config)
    assert user.active_organization is not None


@pytest.mark.django_db
def test_user_active_organization_counters():
    input_args = parse_input_args(['init', 'test', '--username', 'default@localhost', '--password', '12345678'])
    user = _create_user(input_args, {})

    project_config = dict(
        title='Test',
        is_published=True,
        label_config="""
                <View>
                  <Text name="location" value="$location"></Text>
                  <Choices name="text_class" choice="single">
                    <Choice value="class_A"></Choice>
                    <Choice value="class_B"></Choice>
                  </Choices>
                </View>""",
    )

    def make_test_project():
        project = make_project(project_config, user, False, org=user.active_organization)
        task1 = make_task({'data': {'location': 'London', 'text': 'text A'}}, project)
        task2 = make_task({'data': {'location': 'London', 'text': 'text A'}}, project)
        make_annotation({'result': [{'result': [{'r': 1}], 'ground_truth': True}], 'completed_by': user}, task1.id)
        make_annotation({'result': [{'result': [{'r': 1}], 'ground_truth': True}], 'completed_by': user}, task1.id)
        make_annotation({'result': [{'result': [{'r': 1}], 'ground_truth': True}], 'completed_by': user}, task2.id)

    make_test_project()
    make_test_project()
    make_test_project()

    assert user.active_organization_annotations().count() == 9
    assert user.active_organization_contributed_project_number() == 3


# ---------------------------------------------------------------------------
# CLI entry unit tests (parameter parsing & default behaviour)
# ---------------------------------------------------------------------------


class TestArgparserDefaults:
    """Defaults for parse_input_args when running with no command."""

    def test_no_command_parses_without_error(self):
        args = parse_input_args([])
        assert args.command is None

    def test_default_port_is_none(self):
        args = parse_input_args([])
        assert args.port is None

    def test_default_host_is_empty_string(self):
        args = parse_input_args([])
        assert args.host == ''

    def test_default_internal_host_is_zero_zero_zero_zero(self):
        args = parse_input_args([])
        assert args.internal_host == '0.0.0.0'

    def test_default_data_dir_is_none(self):
        args = parse_input_args([])
        assert args.data_dir is None

    def test_default_log_level_is_warning(self):
        args = parse_input_args([])
        assert args.log_level == 'WARNING'

    def test_default_debug_is_false(self):
        args = parse_input_args([])
        assert args.debug is False

    def test_label_config_attribute_is_always_present(self):
        # argparser explicitly adds label_config even if absent from parser
        args = parse_input_args([])
        assert hasattr(args, 'label_config')


class TestArgparserVersion:
    """Parsing of `version` subcommand and `--version` flag."""

    def test_version_subcommand_is_parsed(self):
        args = parse_input_args(['version'])
        assert args.command == 'version'

    def test_version_flag_is_parsed_at_root_level(self):
        args = parse_input_args(['--version'])
        assert args.version is True
        assert args.command is None

    def test_version_subcommand_inherits_root_options(self):
        args = parse_input_args(['version', '--debug'])
        assert args.command == 'version'
        assert args.debug is True


class TestArgparserStartCommand:
    """Parsing of `start` subcommand and associated flags."""

    def test_start_command_parses_without_project_name(self):
        args = parse_input_args(['start'])
        assert args.command == 'start'
        assert args.project_name == ''

    def test_start_command_accepts_project_name(self):
        args = parse_input_args(['start', 'my-project'])
        assert args.command == 'start'
        assert args.project_name == 'my-project'

    def test_start_command_parses_port_flag(self):
        args = parse_input_args(['start', '--port', '7777'])
        assert args.command == 'start'
        assert args.port == 7777

    def test_start_command_parses_short_p_for_port(self):
        args = parse_input_args(['start', '-p', '7788'])
        assert args.port == 7788

    def test_start_command_parses_host_flag(self):
        args = parse_input_args(['start', '--host', 'http://example.com'])
        assert args.host == 'http://example.com'

    def test_start_command_parses_data_dir_flag(self):
        args = parse_input_args(['start', '--data-dir', '/tmp/ls-data'])
        assert args.data_dir == '/tmp/ls-data'

    def test_start_command_parses_database_flag(self):
        args = parse_input_args(['start', '--database', '/tmp/ls.sqlite'])
        assert args.database == '/tmp/ls.sqlite'

    def test_start_command_parses_internal_host_flag(self):
        args = parse_input_args(['start', '--internal-host', '127.0.0.1'])
        assert args.internal_host == '127.0.0.1'

    def test_start_command_parses_log_level_flag(self):
        args = parse_input_args(['start', '--log-level', 'DEBUG'])
        assert args.log_level == 'DEBUG'

    def test_start_command_parses_multiple_flags_together(self):
        args = parse_input_args(
            [
                'start',
                'my-project',
                '--port',
                '9090',
                '--host',
                'http://ls.example.com',
                '--data-dir',
                '/tmp/ls',
                '--debug',
            ]
        )
        assert args.command == 'start'
        assert args.project_name == 'my-project'
        assert args.port == 9090
        assert args.host == 'http://ls.example.com'
        assert args.data_dir == '/tmp/ls'
        assert args.debug is True

    def test_port_flag_without_subcommand(self):
        args = parse_input_args(['--port', '5555'])
        assert args.command is None
        assert args.port == 5555

    def test_host_flag_without_subcommand(self):
        args = parse_input_args(['--host', 'http://localhost'])
        assert args.command is None
        assert args.host == 'http://localhost'

    def test_data_dir_flag_without_subcommand(self):
        args = parse_input_args(['--data-dir', '/tmp/ls-dir'])
        assert args.command is None
        assert args.data_dir == '/tmp/ls-dir'


class TestArgparserInitAndOtherCommands:
    """Lightweight sanity checks for other sub-commands."""

    def test_init_command_with_project_name(self):
        args = parse_input_args(['init', 'my-project'])
        assert args.command == 'init'
        assert args.project_name == 'my-project'

    def test_init_command_has_quiet_mode(self):
        args = parse_input_args(['init', 'proj', '-q'])
        assert args.quiet_mode is True

    def test_unknown_command_fails(self):
        with pytest.raises(SystemExit):
            parse_input_args(['totally-unknown-subcommand'])

    def test_bad_log_level_value_fails(self):
        with pytest.raises(SystemExit):
            parse_input_args(['start', '--log-level', 'NOT_A_LEVEL'])

    def test_non_integer_port_fails(self):
        with pytest.raises(SystemExit):
            parse_input_args(['start', '--port', 'not-a-number'])


# ---------------------------------------------------------------------------
# Unit tests for server helper functions
# ---------------------------------------------------------------------------


class TestCheckPortInUse:
    """Direct tests of check_port_in_use using socket.connect_ex mocking."""

    def test_port_in_use_returns_true(self):
        from label_studio import server as ls_server

        with patch.object(ls_server.socket.socket, 'connect_ex', return_value=0):
            assert ls_server.check_port_in_use('localhost', 8080) is True

    def test_port_free_returns_false(self):
        from label_studio import server as ls_server

        with patch.object(ls_server.socket.socket, 'connect_ex', return_value=10061):
            assert ls_server.check_port_in_use('localhost', 8080) is False

    def test_strips_http_and_https_prefixes(self):
        from label_studio import server as ls_server

        recorded_calls = []

        def fake_connect_ex(address):
            recorded_calls.append(address)
            return 1  # not in use

        with patch.object(ls_server.socket.socket, 'connect_ex', side_effect=fake_connect_ex):
            ls_server.check_port_in_use('http://myhost.example.com', 1234)
        host, _port = recorded_calls[0]
        assert host == 'myhost.example.com'

        recorded_calls.clear()
        with patch.object(ls_server.socket.socket, 'connect_ex', side_effect=fake_connect_ex):
            ls_server.check_port_in_use('https://myhost.example.com', 5678)
        host, _port = recorded_calls[0]
        assert host == 'myhost.example.com'


class TestGetFreePort:
    """Direct tests of _get_free_port helper function."""

    def test_returns_port_directly_when_debug_is_enabled(self):
        from label_studio import server as ls_server

        # in debug mode we short-circuit the availability check
        assert ls_server._get_free_port(8080, True) == 8080

    def test_returns_port_when_not_in_use(self):
        from label_studio import server as ls_server

        with patch.object(ls_server, 'check_port_in_use', return_value=False):
            assert ls_server._get_free_port(8080, False) == 8080

    def test_increments_port_until_free(self):
        from label_studio import server as ls_server

        call_counter = {'n': 0}

        def fake_check_port_in_use(host, port):
            # first two attempts report "in use", then free
            call_counter['n'] += 1
            return port < 8082

        with patch.object(ls_server, 'check_port_in_use', side_effect=fake_check_port_in_use):
            chosen = ls_server._get_free_port(8080, False)
        assert chosen == 8082
        assert call_counter['n'] == 3


# ---------------------------------------------------------------------------
# Mocked integration tests for main() entrypoint
# ---------------------------------------------------------------------------


class TestMainEntrypoint:
    """Mock-heavy tests that exercise main() without actually starting the server."""

    def test_version_command_prints_version(self):
        from label_studio.core.utils import common  # noqa: F401  (ensures submodule import)
        from label_studio import server as ls_server

        fake_versions = {'label-studio-os-package': '0.0.0'}
        with patch.object(
            ls_server, 'parse_input_args', return_value=MagicMock(
                command='version', version=False, log_level=None, database=None,
                data_dir=None, host='', cert_file=None, key_file=None,
                internal_host='0.0.0.0', port=None, debug=False, username=None,
            ),
        ), patch.object(ls_server, '_setup_env'), patch.object(
            ls_server, '_apply_database_migrations'
        ), patch(
            'label_studio.core.utils.common.collect_versions', return_value=fake_versions
        ), patch('builtins.print') as mock_print:
            ls_server.main()
        joined_output = ' '.join(str(c.args) for c in mock_print.mock_calls)
        assert 'Label Studio version' in joined_output

    def test_version_flag_at_root_prints_version(self):
        from label_studio.core.utils import common  # noqa: F401
        from label_studio import server as ls_server

        fake_versions = {'label-studio-os-package': '0.0.0'}
        with patch.object(
            ls_server, 'parse_input_args', return_value=MagicMock(
                command=None, version=True, log_level=None, database=None,
                data_dir=None, host='', cert_file=None, key_file=None,
                internal_host='0.0.0.0', port=None, debug=False, username=None,
            ),
        ), patch.object(ls_server, '_setup_env'), patch.object(
            ls_server, '_apply_database_migrations'
        ), patch(
            'label_studio.core.utils.common.collect_versions', return_value=fake_versions
        ), patch('builtins.print') as mock_print:
            ls_server.main()
        joined_output = ' '.join(str(c.args) for c in mock_print.mock_calls)
        assert 'Label Studio version' in joined_output

    def test_log_level_sets_env_variable(self):
        from label_studio.core.utils import common  # noqa: F401
        from label_studio import server as ls_server

        with patch.object(
            ls_server, 'parse_input_args', return_value=MagicMock(
                command='version', version=False, log_level='DEBUG', database=None,
                data_dir=None, host='', cert_file=None, key_file=None,
                internal_host='0.0.0.0', port=None, debug=False, username=None,
            ),
        ), patch.object(ls_server, '_setup_env'), patch.object(
            ls_server, '_apply_database_migrations'
        ), patch(
            'label_studio.core.utils.common.collect_versions', return_value={}
        ), patch(
            'builtins.print'
        ), patch.dict(os.environ, {}, clear=False):
            os.environ.pop('LOG_LEVEL', None)
            ls_server.main()
            assert os.environ.get('LOG_LEVEL') == 'DEBUG'

    def test_database_flag_sets_database_name_env(self):
        from label_studio.core.utils import common  # noqa: F401
        from label_studio import server as ls_server

        with patch.object(
            ls_server, 'parse_input_args', return_value=MagicMock(
                command='version', version=False, log_level=None, database='/tmp/test.sqlite',
                data_dir=None, host='', cert_file=None, key_file=None,
                internal_host='0.0.0.0', port=None, debug=False, username=None,
            ),
        ), patch.object(ls_server, '_setup_env'), patch.object(
            ls_server, '_apply_database_migrations'
        ), patch(
            'label_studio.core.utils.common.collect_versions', return_value={}
        ), patch(
            'builtins.print'
        ), patch.dict(os.environ, {}, clear=False):
            os.environ.pop('DATABASE_NAME', None)
            ls_server.main()
            assert os.environ['DATABASE_NAME'] == '/tmp/test.sqlite'

    def test_data_dir_flag_sets_label_studio_base_data_dir_env(self):
        from label_studio.core.utils import common  # noqa: F401
        from label_studio import server as ls_server

        with patch.object(
            ls_server, 'parse_input_args', return_value=MagicMock(
                command='version', version=False, log_level=None, database=None,
                data_dir='/tmp/ls-data', host='', cert_file=None, key_file=None,
                internal_host='0.0.0.0', port=None, debug=False, username=None,
            ),
        ), patch.object(ls_server, '_setup_env'), patch.object(
            ls_server, '_apply_database_migrations'
        ), patch(
            'label_studio.core.utils.common.collect_versions', return_value={}
        ), patch(
            'builtins.print'
        ), patch.dict(os.environ, {}, clear=False):
            os.environ.pop('LABEL_STUDIO_BASE_DATA_DIR', None)
            ls_server.main()
            assert os.environ['LABEL_STUDIO_BASE_DATA_DIR'] == '/tmp/ls-data'

    def test_host_flag_sets_host_env(self):
        from label_studio.core.utils import common  # noqa: F401
        from label_studio import server as ls_server

        with patch.object(
            ls_server, 'parse_input_args', return_value=MagicMock(
                command='version', version=False, log_level=None, database=None,
                data_dir=None, host='http://example.com', cert_file=None, key_file=None,
                internal_host='0.0.0.0', port=None, debug=False, username=None,
            ),
        ), patch.object(ls_server, '_setup_env'), patch.object(
            ls_server, '_apply_database_migrations'
        ), patch(
            'label_studio.core.utils.common.collect_versions', return_value={}
        ), patch(
            'builtins.print'
        ), patch.dict(os.environ, {}, clear=False):
            os.environ.pop('HOST', None)
            ls_server.main()
            assert os.environ['HOST'] == 'http://example.com'

    def _make_start_args(self, **overrides):
        defaults = dict(
            command='start', version=False, log_level=None, database=None,
            data_dir=None, host='', cert_file=None, key_file=None,
            internal_host='0.0.0.0', port=None, debug=False, username=None,
            project_name='',
        )
        defaults.update(overrides)
        return MagicMock(**defaults)

    def test_start_command_calls_app_run_with_internal_host_and_port(self):
        from label_studio.core.utils import common  # noqa: F401
        from label_studio import server as ls_server

        args = self._make_start_args(port=9191, internal_host='127.0.0.1')
        with patch.object(ls_server, 'parse_input_args', return_value=args), patch.object(
            ls_server, '_setup_env'
        ), patch.object(ls_server, '_apply_database_migrations'), patch(
            'label_studio.core.utils.common.collect_versions', return_value={}
        ), patch('label_studio.core.utils.common.start_browser'), patch.object(
            ls_server, '_get_free_port', return_value=9191
        ) as mock_free_port, patch.object(
            ls_server, '_app_run'
        ) as mock_app_run, patch.dict(os.environ, {}, clear=False):
            os.environ.pop('PORT', None)
            ls_server.main()
        mock_free_port.assert_called_once()
        mock_app_run.assert_called_once_with(host='127.0.0.1', port=9191)

    def test_start_command_defaults_config_port_when_port_unset(self):
        from label_studio.core.utils import common  # noqa: F401
        from label_studio import server as ls_server

        args = self._make_start_args(port=None)
        with patch.object(ls_server, 'parse_input_args', return_value=args), patch.object(
            ls_server, '_setup_env'
        ), patch.object(ls_server, '_apply_database_migrations'), patch(
            'label_studio.core.utils.common.collect_versions', return_value={}
        ), patch('label_studio.core.utils.common.start_browser'), patch.object(
            ls_server, '_get_free_port', return_value=8080
        ) as mock_free_port, patch.object(
            ls_server, '_app_run'
        ) as mock_app_run, patch.dict(os.environ, {'PORT': '9090'}, clear=False):
            ls_server.main()
        # internal_port is resolved from env PORT of 9090 in main() then passed
        # to _get_free_port as an integer
        call_args, _ = mock_free_port.call_args
        assert call_args[0] == 9090
        mock_app_run.assert_called_once_with(host='0.0.0.0', port=8080)

    def test_default_behavior_no_command_starts_server(self):
        from label_studio.core.utils import common  # noqa: F401
        from label_studio import server as ls_server

        args = self._make_start_args(command=None, port=7654, internal_host='0.0.0.0')
        with patch.object(ls_server, 'parse_input_args', return_value=args), patch.object(
            ls_server, '_setup_env'
        ), patch.object(ls_server, '_apply_database_migrations'), patch(
            'label_studio.core.utils.common.collect_versions', return_value={}
        ), patch('label_studio.core.utils.common.start_browser'), patch.object(
            ls_server, '_get_free_port', return_value=7654
        ), patch.object(ls_server, '_app_run') as mock_app_run, patch.dict(
            os.environ, {}, clear=False
        ):
            os.environ.pop('PORT', None)
            ls_server.main()
        mock_app_run.assert_called_once_with(host='0.0.0.0', port=7654)

    def test_ssl_cert_is_rejected_without_starting_server(self):
        from label_studio.core.utils import common  # noqa: F401
        from label_studio import server as ls_server

        args = self._make_start_args(cert_file='/tmp/fake.pem', key_file=None)
        with patch.object(ls_server, 'parse_input_args', return_value=args), patch.object(
            ls_server, '_setup_env'
        ), patch.object(ls_server, '_apply_database_migrations'), patch(
            'label_studio.core.utils.common.collect_versions', return_value={}
        ), patch.object(ls_server, '_app_run') as mock_app_run, patch(
            'label_studio.core.utils.common.start_browser'
        ), patch.dict(os.environ, {}, clear=False):
            ls_server.main()
        mock_app_run.assert_not_called()
