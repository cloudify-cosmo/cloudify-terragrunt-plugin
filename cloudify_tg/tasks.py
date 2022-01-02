from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError

from . import decorators
from .constants import SUPPORTED_TG_COMMANDS_OPTIONS, SUPPORTED_TG_COMMANDS


@operation
@decorators.with_terragrunt
def precreate(tg, **_):
    tg.terragrunt_info()
    tg.graph_dependencies()
    tg.validate_inputs()
    tg.plan()


@operation
@decorators.with_terragrunt
def create(tg, **_):
    tg.apply()


@operation
@decorators.with_terragrunt
def poststart(tg, **_):
    tg.output()


@operation
@decorators.with_terragrunt
def delete(tg, **_):
    tg.destroy()


@operation
@decorators.with_terragrunt
def terragrunt_plan(tg, **_):
    tg.plan()


@operation
@decorators.with_terragrunt
def terragrunt_destroy(tg, **_):
    tg.destroy()


@operation
@decorators.with_terragrunt
def terragrunt_output(tg, **_):
    tg.output()


@operation
@decorators.with_terragrunt
def terragrunt_apply(tg, **_):
    tg.apply()


@operation
@decorators.with_terragrunt
def terragrunt_info(tg, **_):
    tg.terragrunt_info()


@operation
@decorators.with_terragrunt
def validate_inputs(tg, **_):
    tg.validate_inputs()


@operation
@decorators.with_terragrunt
def graph_dependencies(tg, **_):
    tg.graph_dependencies()


@operation
@decorators.with_terragrunt
def render_json(tg, **_):
    tg.render_json()


@operation
@decorators.with_terragrunt
def run_command(command, tg, options=None, force=False, *_, **__):

    if command.startswith('run-all'):
        ___, command = command.split(' ')
        tg.run_all = True

    options = options or {}
    if command not in SUPPORTED_TG_COMMANDS and not force:
        raise NonRecoverableError(
            'command: {} ,not in SUPPORTED_TG_COMMANDS: {}'
            .format(command, SUPPORTED_TG_COMMANDS))

    if SUPPORTED_TG_COMMANDS_OPTIONS.__contains__(options):
        raise NonRecoverableError(
            'options: {} ,not in SUPPORTED_TG_COMMANDS_OPTIONS: {} '
            .format(options, SUPPORTED_TG_COMMANDS_OPTIONS))

    tg.update_command_options({command: options})
    tg.execute(command)
