"""This file and its contents are licensed under the Apache License 2.0. Please see the included NOTICE for copyright information and LICENSE for a copy of the license."""

import os
import sys
from unittest import mock

import pytest
from server import _create_user, main
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


def test_parse_input_args_version_flag():
    args = parse_input_args(['--version'])
    assert args.version is True
    assert args.command is None


def test_parse_input_args_version_command():
    args = parse_input_args(['version'])
    assert args.command == 'version'


def test_parse_input_args_start_command():
    args = parse_input_args(['start'])
    assert args.command == 'start'
    assert args.project_name == ''


def test_parse_input_args_start_with_project():
    args = parse_input_args(['start', 'my_project'])
    assert args.command == 'start'
    assert args.project_name == 'my_project'


def test_parse_input_args_no_command():
    args = parse_input_args([])
    assert args.command is None


def test_parse_input_args_port_short_option():
    args = parse_input_args(['start', '-p', '9090'])
    assert args.port == 9090


def test_parse_input_args_port_long_option():
    args = parse_input_args(['start', '--port', '9090'])
    assert args.port == 9090


def test_parse_input_args_host():
    args = parse_input_args(['start', '--host', 'https://example.com'])
    assert args.host == 'https://example.com'


def test_parse_input_args_internal_host():
    args = parse_input_args(['start', '--internal-host', '127.0.0.1'])
    assert args.internal_host == '127.0.0.1'


def test_parse_input_args_data_dir():
    args = parse_input_args(['start', '--data-dir', '/custom/data/dir'])
    assert args.data_dir == '/custom/data/dir'


def test_parse_input_args_database():
    args = parse_input_args(['start', '--database', '/path/to/mydb.sqlite3'])
    assert args.database == '/path/to/mydb.sqlite3'


def test_parse_input_args_no_browser_short():
    args = parse_input_args(['start', '-b'])
    assert args.no_browser is True


def test_parse_input_args_no_browser_long():
    args = parse_input_args(['start', '--no-browser'])
    assert args.no_browser is True


def test_parse_input_args_debug():
    args = parse_input_args(['start', '--debug'])
    assert args.debug is True


def test_parse_input_args_log_level():
    args = parse_input_args(['start', '--log-level', 'DEBUG'])
    assert args.log_level == 'DEBUG'


def test_main_version_command_outputs(capsys):
    with mock.patch.object(sys, 'argv', ['label-studio', 'version']):
        with mock.patch('server._setup_env'):
            with mock.patch('server._apply_database_migrations'):
                with mock.patch('label_studio.core.utils.common.collect_versions') as mock_collect:
                    mock_collect.return_value = {'release': '1.0.0'}
                    main()
    output = capsys.readouterr().out
    assert 'Label Studio version' in output
    assert '1.0.0' in output


def test_main_version_flag_also_starts_server():
    with mock.patch.object(sys, 'argv', ['label-studio', '--version']):
        with mock.patch('server._setup_env'):
            with mock.patch('server._apply_database_migrations'):
                with mock.patch('server._create_user'):
                    with mock.patch('server._app_run') as mock_app_run:
                        main()
                        mock_app_run.assert_called_once()


def test_main_sets_log_level_env():
    with mock.patch.object(sys, 'argv', ['label-studio', 'start', '--log-level', 'ERROR']):
        with mock.patch('server._setup_env'):
            with mock.patch('server._apply_database_migrations'):
                with mock.patch('server._app_run'):
                    with mock.patch('server._create_user'):
                        original_env = os.environ.get('LOG_LEVEL')
                        try:
                            if 'LOG_LEVEL' in os.environ:
                                del os.environ['LOG_LEVEL']
                            main()
                            assert os.environ.get('LOG_LEVEL') == 'ERROR'
                        finally:
                            if original_env is not None:
                                os.environ['LOG_LEVEL'] = original_env
                            elif 'LOG_LEVEL' in os.environ:
                                del os.environ['LOG_LEVEL']


def test_main_sets_database_env():
    custom_db = '/custom/path/db.sqlite3'
    with mock.patch.object(sys, 'argv', ['label-studio', 'start', '--database', custom_db]):
        with mock.patch('server._setup_env'):
            with mock.patch('server._apply_database_migrations'):
                with mock.patch('server._app_run'):
                    with mock.patch('server._create_user'):
                        original_env = os.environ.get('DATABASE_NAME')
                        try:
                            if 'DATABASE_NAME' in os.environ:
                                del os.environ['DATABASE_NAME']
                            main()
                            assert os.environ.get('DATABASE_NAME') == custom_db
                        finally:
                            if original_env is not None:
                                os.environ['DATABASE_NAME'] = original_env
                            elif 'DATABASE_NAME' in os.environ:
                                del os.environ['DATABASE_NAME']


def test_main_sets_data_dir_env():
    custom_data_dir = '/custom/data/dir'
    with mock.patch.object(sys, 'argv', ['label-studio', 'start', '--data-dir', custom_data_dir]):
        with mock.patch('server._setup_env'):
            with mock.patch('server._apply_database_migrations'):
                with mock.patch('server._app_run'):
                    with mock.patch('server._create_user'):
                        original_env = os.environ.get('LABEL_STUDIO_BASE_DATA_DIR')
                        try:
                            if 'LABEL_STUDIO_BASE_DATA_DIR' in os.environ:
                                del os.environ['LABEL_STUDIO_BASE_DATA_DIR']
                            main()
                            assert os.environ.get('LABEL_STUDIO_BASE_DATA_DIR') == custom_data_dir
                        finally:
                            if original_env is not None:
                                os.environ['LABEL_STUDIO_BASE_DATA_DIR'] = original_env
                            elif 'LABEL_STUDIO_BASE_DATA_DIR' in os.environ:
                                del os.environ['LABEL_STUDIO_BASE_DATA_DIR']


def test_main_sets_host_env():
    custom_host = 'https://my.example.com'
    with mock.patch.object(sys, 'argv', ['label-studio', 'start', '--host', custom_host]):
        with mock.patch('server._setup_env'):
            with mock.patch('server._apply_database_migrations'):
                with mock.patch('server._app_run'):
                    with mock.patch('server._create_user'):
                        original_env = os.environ.get('HOST')
                        try:
                            if 'HOST' in os.environ:
                                del os.environ['HOST']
                            main()
                            assert os.environ.get('HOST') == custom_host
                        finally:
                            if original_env is not None:
                                os.environ['HOST'] = original_env
                            elif 'HOST' in os.environ:
                                del os.environ['HOST']


def test_main_start_with_port_option_uses_provided_port():
    test_port = 9090
    with mock.patch.object(sys, 'argv', ['label-studio', 'start', '--port', str(test_port)]):
        with mock.patch('server._setup_env'):
            with mock.patch('server._apply_database_migrations'):
                with mock.patch('server._create_user'):
                    with mock.patch('server._get_free_port') as mock_get_free_port:
                        mock_get_free_port.return_value = test_port
                        with mock.patch('server._app_run') as mock_app_run:
                            main()
                            mock_app_run.assert_called_once()
                            args = mock_app_run.call_args
                            assert args[1]['port'] == test_port


def test_main_start_with_port_env_fallback(monkeypatch):
    test_port = 8888
    monkeypatch.setenv('PORT', str(test_port))
    with mock.patch.object(sys, 'argv', ['label-studio', 'start']):
        with mock.patch('server._setup_env'):
            with mock.patch('server._apply_database_migrations'):
                with mock.patch('server._create_user'):
                    with mock.patch('server._get_free_port') as mock_get_free_port:
                        mock_get_free_port.return_value = test_port
                        with mock.patch('server._app_run') as mock_app_run:
                            main()
                            mock_app_run.assert_called_once()
                            args = mock_app_run.call_args
                            assert args[1]['port'] == test_port


def test_main_default_behavior_no_command():
    with mock.patch.object(sys, 'argv', ['label-studio']):
        with mock.patch('server._setup_env'):
            with mock.patch('server._apply_database_migrations'):
                with mock.patch('server._create_user'):
                    with mock.patch('server._app_run') as mock_app_run:
                        main()
                        mock_app_run.assert_called_once()


def test_main_start_with_custom_internal_host():
    custom_host = '127.0.0.1'
    with mock.patch.object(sys, 'argv', ['label-studio', 'start', '--internal-host', custom_host]):
        with mock.patch('server._setup_env'):
            with mock.patch('server._apply_database_migrations'):
                with mock.patch('server._create_user'):
                    with mock.patch('server._get_free_port'):
                        with mock.patch('server._app_run') as mock_app_run:
                            main()
                            mock_app_run.assert_called_once()
                            args = mock_app_run.call_args
                            assert args[1]['host'] == custom_host
