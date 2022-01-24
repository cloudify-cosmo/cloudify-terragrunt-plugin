from .. import constants


def test_supported_tg_commands():
    assert 'run-all' in constants.SUPPORTED_TG_COMMANDS
    assert 'plan' in constants.SUPPORTED_TG_COMMANDS
    assert 'apply' in constants.SUPPORTED_TG_COMMANDS
    assert 'output' in constants.SUPPORTED_TG_COMMANDS
    assert 'destroy' in constants.SUPPORTED_TG_COMMANDS
    assert 'validate' in constants.SUPPORTED_TG_COMMANDS
    assert 'terragrunt-info' in constants.SUPPORTED_TG_COMMANDS
    assert 'validate-inputs' in constants.SUPPORTED_TG_COMMANDS
    assert 'graph-dependencies' in constants.SUPPORTED_TG_COMMANDS
    assert 'aws-provider-patch' in constants.SUPPORTED_TG_COMMANDS
    assert 'render-json' in constants.SUPPORTED_TG_COMMANDS
    assert len(constants.SUPPORTED_TG_COMMANDS) == 12


def test_command_options():
    for item in constants.SUPPORTED_TG_COMMANDS_OPTIONS:
        if 'terragrunt' in item:
            assert item.startswith('--')
        else:
            assert item in ['debug', '-auto-approve', '-json']


def test_mask_env():
    assert 'AWS_SECRET_ACCESS_KEY' in constants.MASKED_ENV_VARS
    assert 'AWS_ACCESS_KEY_ID' in constants.MASKED_ENV_VARS
    assert 'AWS_DEFAULT_REGION' in constants.MASKED_ENV_VARS
