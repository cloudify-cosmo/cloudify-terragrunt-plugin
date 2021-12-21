import os
from copy import deepcopy
from shutil import rmtree

from cloudify import ctx as ctx_from_imports
from cloudify_common_sdk import (
    get_ctx_node,
    get_ctx_instance,
    get_deployment_dir,
    get_shared_resource)
from cloudify_common_sdk.processes import general_executor, process_execution

from tg_sdk import Terragrunt


# SHOULD_BE_USER_PROVIDED
MASKED_ENV_VARS = {}


def terragrunt_from_ctx(ctx):
    ctx_node = get_ctx_node()
    ctx_instance = get_ctx_instance()
    return Terragrunt(
        ctx_node,
        logger=ctx.logger,
        executor=run,
        cwd=get_deployment_dir(ctx.deployment.id),
        **ctx_instance.runtime_properties.get('resource_config', {})
    )


def run(command,
        logger=None,
        cwd=None,
        env=None,
        additional_args=None,
        return_output=False):
    """Execute a shell script or command."""

    logger = logger or ctx_from_imports.logger
    cwd = cwd or get_node_instance_dir()

    if additional_args is None:
        additional_args = {}

    args_to_pass = deepcopy(additional_args)

    if env:
        passed_env = args_to_pass.setdefault('env', {})
        passed_env.update(os.environ)
        passed_env.update(env)

    printed_args = deepcopy(args_to_pass)
    printed_env = printed_args.get('env', {})
    for env_var in printed_env.keys():
        if env_var in MASKED_ENV_VARS:
            printed_env[env_var] = '****'

    logger.info('Running: command={cmd}, '
                'cwd={cwd}, '
                'additional_args={args}'.format(
                    cmd=command,
                    cwd=cwd,
                    args=printed_args))

    general_executor_params = deepcopy(args_to_pass)
    general_executor_params['cwd'] = cwd
    if 'log_stdout' not in general_executor_params:
        general_executor_params['log_stdout'] = return_output
    if 'log_stderr' not in general_executor_params:
        general_executor_params['log_stderr'] = True
    if 'stderr_to_stdout' not in general_executor_params:
        general_executor_params['stderr_to_stdout'] = False
    script_path = command.pop(0)
    general_executor_params['args'] = command
    general_executor_params['max_sleep_time'] = get_ctx_node().properties.get(
        'max_sleep_time', 300)

    return process_execution(
        general_executor,
        script_path,
        ctx_from_imports,
        general_executor_params)


# Merge with TF Plugin
def get_node_instance_dir(target=False, source=False, source_path=None):
    """This is the place where the magic happens.
    We put all our binaries, templates, or symlinks to those files here,
    and then we also run all executions from here.
    """
    instance = get_ctx_instance(target=target, source=source)
    folder = os.path.join(
        get_deployment_dir(ctx_from_imports.deployment.id),
        instance.id
    )
    if source_path:
        folder = os.path.join(folder, source_path)
    if not os.path.exists(folder):
        mkdir_p(folder)
    ctx_from_imports.logger.debug('Value deployment_dir is {loc}.'.format(
        loc=folder))
    return folder


def download_terragrunt_source(source):
    """Replace the terraform_source material with a new material.
    This is used in terraform.reload_template operation."""
    ctx_from_imports.logger.info(
        'Using this cloudify.types.terragrunt.SourceSpecification '
        '{source}.'.format(source=source))
    node_instance_dir = get_node_instance_dir()
    if isinstance(source, dict):
        ctx_from_imports.logger.info('Downloading {source} to {dest}.'.format(
            source=source, dest=node_instance_dir))
        source_tmp_path = get_shared_resource(
            source, dir=node_instance_dir,
            username=source.get('username'),
            password=source.get('password'))
        ctx_from_imports.logger.info('Temporary Terragrunt source {}'.format(
            source_tmp_path))
        copy_directory(source_tmp_path, node_instance_dir)
        remove_directory(source_tmp_path)


def cleanup_old_terragrunt_source():
    node_instance_dir = get_node_instance_dir()
    paths_to_delete = []
    for files in os.listdir(node_instance_dir):
        path = os.path.join(node_instance_dir, files)
        paths_to_delete.append(path)
    ctx_from_imports.logger.info('Deleting these paths {}.'.format(
        paths_to_delete))
    for path in paths_to_delete:
        try:
            rmtree(path)
        except OSError:
            os.remove(path)


# Merge with TF Plugin
def copy_directory(src, dst):
    run(['cp', '-r', os.path.join(src, '*'), dst])


# Merge with TF Plugin
def remove_directory(dir):
    run(['rm', '-rf', dir])


# Merge with TF Plugin
def mkdir_p(path):
    import pathlib
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)
