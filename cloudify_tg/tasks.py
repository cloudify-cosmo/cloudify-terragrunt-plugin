import os
from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError

from . import utils
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


@operation
@decorators.skip_if_existing
def install(ctx, **_):
    # folder
    installation_dir = utils.get_node_instance_dir()
    # The path to the terragrunt binary executable.
    executable_path = utils.get_executable_path()
    # Location to download the Terraform executable binary from.
    installation_source = utils.get_installation_source()

    if os.path.isfile(executable_path):
        ctx.logger.info(
            'Terragrunt executable already found at {path}; '
            'skipping installation of executable'.format(
                path=executable_path))
    else:
        ctx.logger.warn('You are requesting to write a new file to {loc}. '
                        'If you do not have sufficient permissions, that '
                        'installation will fail.'.format(
                            loc=executable_path))

        binary_name = "terragrunt"
        utils.install_binary(os.path.join(installation_dir, binary_name),
                             executable_path, installation_source)

    ctx.instance.runtime_properties['executable_path'] = executable_path


@operation
@decorators.skip_if_existing
def uninstall(ctx, **_):
    terragrunt_config = utils.get_terragrunt_config()
    resource_config = utils.get_resource_config()
    exc_path = terragrunt_config.get('executable_path', '')
    system_exc = resource_config.get('use_existing_resource')

    if os.path.isfile(exc_path):
        if system_exc:
            ctx.logger.info(
                'Not removing Terragrunt installation at {loc} as'
                'it was provided externally'.format(loc=exc_path))
        else:
            ctx.logger.info('Removing executable: {path}'.format(
                path=exc_path))
            os.remove(exc_path)
