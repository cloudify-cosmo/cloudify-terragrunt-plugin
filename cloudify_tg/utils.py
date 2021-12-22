import os
from copy import deepcopy
from shutil import rmtree

from cloudify import ctx as ctx_from_imports
from cloudify_common_sdk.utils import (
    get_ctx_node,
    get_ctx_instance,
    get_deployment_dir,
    get_shared_resource)
from cloudify_common_sdk.processes import general_executor, process_execution

from tg_sdk import Terragrunt, utils as tg_sdk_utils


# SHOULD_BE_USER_PROVIDED
MASKED_ENV_VARS = {}


def configure_ctx(ctx_instance, ctx_node, resource_config=None):
    if 'resource_config' not in ctx_instance.runtime_properties:
        ctx_instance.runtime_properties['resource_config'] = \
            resource_config or  ctx_node.properties['resource_config']
    return ctx_instance.runtime_properties['resource_config']


def terragrunt_from_ctx(kwargs):
    _ctx = kwargs.get('ctx')
    ctx_node = get_ctx_node(_ctx)
    ctx_instance = get_ctx_instance(_ctx)
    ctx = _ctx or ctx_from_imports
    configure_ctx(ctx_instance, ctx_node, kwargs.get('resource_config', {}))
    tg = Terragrunt(
        ctx_node,
        logger=ctx.logger,
        executor=run,
        cwd=get_deployment_dir(ctx.deployment.id),
        **ctx_instance.runtime_properties['resource_config']
    )
    update_source = kwargs.get('update_source', False)
    if update_source:
        cleanup_old_terragrunt_source()
    # Maybe we want to update it if it already exists.
    # Maybe we need to download a new source.
    with tg.update_source_path(update_source) as source:
        download_terragrunt_source(source)
    return tg


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


def download_terragrunt_source(source):
    """Replace the terraform_source material with a new material.
    This is used in terraform.reload_template operation."""
    ctx_from_imports.logger.info(
        'Using this cloudify.types.terragrunt.SourceSpecification '
        '{source}.'.format(source=source))
    node_instance_dir = get_node_instance_dir()
    source_tmp_path = tg_sdk_utils.download_source(
        source, node_instance_dir, ctx_from_imports.logger)
    copy_directory(source_tmp_path, node_instance_dir)
    remove_directory(source_tmp_path)


def get_terragrunt_source_config(new_source_config=False):
    """Source config can be either
    { 'location': URL, 'username': 'foo'', 'password': 'bar'} or URL.
    It should be in the node properties or in the runtime properties


    :param new_source_config: a string or a dict or None
    :return:
    """
    ctx_instance = get_ctx_instance()
    if new_source_config:
        ctx_instance.runtime_properties['resource_config']['source'] = \
            new_source_config
    instance_props = ctx_instance.runtime_properties.get('resource_config', {})
    if 'source' in instance_props:
        return instance_props['source']
    node_props = get_ctx_node().properties['resource_config']
    return node_props['source']


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


# Merge with TF Plugin
def get_node_instance_dir():
    instance = get_ctx_instance()
    folder = os.path.join(
        get_deployment_dir(ctx_from_imports.deployment.id),
        instance.id
    )
    if not os.path.exists(folder):
        mkdir_p(folder)
    ctx_from_imports.logger.debug(
        'Value node_instance_dir is {folder}.'.format(folder=folder))
    return folder
