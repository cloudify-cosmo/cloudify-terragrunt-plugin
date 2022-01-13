from .. import constants


def test_supported_tg_commands():
    assert 'plan' in constants.SUPPORTED_TG_COMMANDS
    assert 'apply' in constants.SUPPORTED_TG_COMMANDS
    assert len(constants.SUPPORTED_TG_COMMANDS) == 12


def test_command_options():
    for item in constants.SUPPORTED_TG_COMMANDS_OPTIONS:
        if 'terragrunt' in item:
            assert item.startswith('--')
