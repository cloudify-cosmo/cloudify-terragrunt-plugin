import os
import json
import shutil
import tempfile
from mock import patch
from unittest.mock import MagicMock

from .. import utils
from .. import Terragrunt


properties = {
    'resource_config': {
        'binary_path': '/usr/local/bin/terragrunt',
        'terraform_binary_path': '/usr/local/bin/terraform',
        'source': 'https://github.com/terragrunt/archive/refs/heads/main.zip',
        'source_path': '',
        'variables': {},
        'environment_variables': {
            'AWS_ACCESS_KEY_ID': '',
            'AWS_SECRET_ACCESS_KEY': '',
            'AWS_DEFAULT_REGION': ''
        },
        'run_all': False,
        'command_options': {
            'all': ['--terragrunt-non-interactive', '--terragrunt-log-level'],
            'apply': ['-auto-approve'],
            'destroy': ['-auto-approve'],
            'plan': ['-json'],
            'output': ['-json']
        }
    }
}

source = 'https://blablabla.zip'
source_path = ''


def test_properties():
    tg = Terragrunt(properties=properties, source=source)
    assert tg.properties == properties


def test_logger():
    tg = Terragrunt(properties=properties, source=source)
    assert tg.logger is None or utils.get_logger('TerragruntLogger')


def test_resource_config():
    tg = Terragrunt(properties=properties, source=source)
    assert tg.resource_config == properties.get('resource_config', {})


def test_source():
    tg = Terragrunt(properties=properties, source=source)
    assert tg.source == source or tg.resource_config.get('source')


def test_source_path():
    tg = Terragrunt(properties=properties, source=source)
    if os.path.exists(source_path):
        assert tg.source_path == source_path or \
               tg.resource_config.get('source_path')
    else:
        assert tg.source_path is None


def test_setter_source_path():
    tg = Terragrunt(properties=properties, source=source)
    source_path_set = tempfile.mkdtemp()
    tg.source_path = source_path_set
    assert tg.source_path == source_path_set, '{}'.format(tg.source_path)
    assert tg.resource_config.get('source_path') == source_path_set
    shutil.rmtree(source_path_set)


def test_binary_path():
    tg = Terragrunt(properties=properties, source=source)
    assert tg.binary_path == tg.resource_config.get('binary_path')


def test_terraform_binary_path():
    mocked_executor = MagicMock()
    mocked_executor.return_value = '1.0.4'

    tg = Terragrunt(properties=properties,
                    source=source,
                    executor=mocked_executor)

    assert tg.terraform_binary_path == \
           tg.resource_config.get('terraform_binary_path')


def test_run_all():
    tg = Terragrunt(properties=properties, source=source)
    assert tg.run_all == tg.resource_config.get('run_all')


def test_setter_run_all():
    tg = Terragrunt(properties=properties, source=source)
    tg.run_all = True
    assert tg.run_all is True


def test_environment_variables():
    tg = Terragrunt(properties=properties, source=source)
    assert tg.environment_variables == \
           tg.resource_config.get('environment_variables')


def test_command_options():
    tg = Terragrunt(properties=properties, source=source)
    assert tg.command_options == tg.resource_config.get('command_options', {})


def test_update_command_options():
    tg = Terragrunt(properties=properties, source=source)
    new_dict = {
        'all': ['--terragrunt-non-interactive', '--terragrunt-log-level',
                'debug'],
        'apply': ['-auto-approve'],
        'destroy': ['-auto-approve'],
        'plan': ['-json'],
        'output': ['-json']
    }

    tg.update_command_options(new_dict)
    assert tg.command_options == new_dict


def test_version():
    mocked_executor = MagicMock()
    mocked_executor.return_value = '100.5.2'
    tg = Terragrunt(properties=properties,
                    source=source,
                    executor=mocked_executor)
    assert tg.version == '100.5.2'


def test__execute():
    mocked_executor = MagicMock()
    tg = Terragrunt(properties=properties,
                    source=source,
                    executor=mocked_executor)
    tg._execute('foo', False)
    mocked_executor.assert_called_once_with(
        'foo',
        logger=tg.logger,
        additional_env=tg.environment_variables,
        return_output=False
    )


def test_execute():
    mocked_executor = MagicMock()
    tg = Terragrunt(properties=properties,
                    source=source,
                    executor=mocked_executor)
    tg.execute('foo', False)
    mocked_executor.assert_called_once_with(
        ['/usr/local/bin/terragrunt',
         'foo',
         '--terragrunt-non-interactive',
         '--terragrunt-log-level',
         '--terragrunt-tfpath',
         '/usr/local/bin/terraform'],
        logger=tg.logger,
        additional_env=tg.environment_variables,
        return_output=False
    )


def test_commands():
    mocked_executor = MagicMock()
    tg = Terragrunt(properties=properties,
                    source=source,
                    executor=mocked_executor)
    tg.render_json()
    mocked_executor.assert_called_once_with(
        ['/usr/local/bin/terragrunt',
         'render-json',
         '--terragrunt-non-interactive',
         '--terragrunt-log-level',
         '--terragrunt-tfpath',
         '/usr/local/bin/terraform'],
        logger=tg.logger,
        additional_env=tg.environment_variables,
        return_output=True
    )

    mocked_executor = MagicMock()
    tg = Terragrunt(properties=properties,
                    source=source,
                    executor=mocked_executor)
    tg.graph_dependencies()
    mocked_executor.assert_called_once_with(
        ['/usr/local/bin/terragrunt',
         'graph-dependencies',
         '--terragrunt-non-interactive',
         '--terragrunt-log-level',
         '--terragrunt-tfpath',
         '/usr/local/bin/terraform'],
        logger=tg.logger,
        additional_env=tg.environment_variables,
        return_output=True
    )

    mocked_executor = MagicMock()
    tg = Terragrunt(properties=properties,
                    source=source,
                    executor=mocked_executor)
    tg.validate_inputs()
    mocked_executor.assert_called_once_with(
        ['/usr/local/bin/terragrunt',
         'validate-inputs',
         '--terragrunt-non-interactive',
         '--terragrunt-log-level',
         '--terragrunt-tfpath',
         '/usr/local/bin/terraform'],
        logger=tg.logger,
        additional_env=tg.environment_variables,
        return_output=True
    )

    mocked_executor = MagicMock()
    tg = Terragrunt(properties=properties,
                    source=source,
                    executor=mocked_executor)
    tg.terragrunt_info()
    mocked_executor.assert_called_once_with(
        ['/usr/local/bin/terragrunt',
         'terragrunt-info',
         '--terragrunt-non-interactive',
         '--terragrunt-log-level',
         '--terragrunt-tfpath',
         '/usr/local/bin/terraform'],
        logger=tg.logger,
        additional_env=tg.environment_variables,
        return_output=True
    )

    mocked_executor = MagicMock()
    tg = Terragrunt(properties=properties,
                    source=source,
                    executor=mocked_executor)
    tg.apply()
    mocked_executor.assert_called_once_with(
        ['/usr/local/bin/terragrunt',
         'apply',
         '--terragrunt-non-interactive',
         '--terragrunt-log-level',
         '-auto-approve',
         '--terragrunt-tfpath',
         '/usr/local/bin/terraform'],
        logger=tg.logger,
        additional_env=tg.environment_variables,
        return_output=True
    )

    mocked_executor = MagicMock()
    tg = Terragrunt(properties=properties,
                    source=source,
                    executor=mocked_executor)
    tg.destroy()
    mocked_executor.assert_called_once_with(
        ['/usr/local/bin/terragrunt',
         'destroy',
         '--terragrunt-non-interactive',
         '--terragrunt-log-level',
         '-auto-approve',
         '--terragrunt-tfpath',
         '/usr/local/bin/terraform'],
        logger=tg.logger,
        additional_env=tg.environment_variables,
        return_output=True
    )


def test_plan():
    mock_returned = '{"foo": "bar"}' \
                 '{"type": "outputs", ' \
                 '"outputs": {"output_foo": "output_bar"}}' \
                 '{"type": "change_summary", ' \
                 '"changes": {"change_foo": "change_bar"}}' \
                 '{"type": "resource_drift", ' \
                 '"change": {"change_foo": "change_bar"}}'
    expected = {
        'resource_drifts': [{'change_foo': 'change_bar'}],
        'outputs': {'output_foo': 'output_bar'},
        'change_summary': {'change_foo': 'change_bar'}
    }

    mocked_executor = MagicMock()
    mocked_executor.return_value = mock_returned
    tg = Terragrunt(properties=properties,
                    source=source,
                    executor=mocked_executor)
    plan = tg.plan()
    assert plan == expected


def test_terraform_plan():
    mock_returned = '{"foo": "bar"}' \
                    '{"type": "outputs", ' \
                    '"outputs": {"output_foo": "output_bar"}}' \
                    '{"type": "change_summary", ' \
                    '"changes": {"change_foo": "change_bar"}}' \
                    '{"type": "resource_drift", ' \
                    '"change": {"change_foo": "change_bar"}}'
    expected = {
        'resource_drifts': [{'change_foo': 'change_bar'}],
        'outputs': {'output_foo': 'output_bar'},
        'change_summary': {'change_foo': 'change_bar'}
    }

    mocked_executor = MagicMock()
    mocked_executor.return_value = mock_returned
    tg = Terragrunt(properties=properties,
                    source=source,
                    executor=mocked_executor)
    plan = tg.plan()

    assert plan == expected


def test_output():
    expected = {'foo': ["bar"]}
    test_json = json.dumps(expected)

    mocked_executor = MagicMock()
    mocked_executor.return_value = test_json
    tg = Terragrunt(properties=properties,
                    source=source,
                    executor=mocked_executor)
    result = tg.output()

    assert result == expected


def test_terraform_output():
    expected = {'foo': ["bar"]}
    test_json = json.dumps(expected)

    mocked_executor = MagicMock()
    mocked_executor.return_value = test_json
    tg = Terragrunt(properties=properties,
                    source=source,
                    executor=mocked_executor)
    result = tg.output()

    assert tg.terraform_output == result
