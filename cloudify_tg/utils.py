import os
from copy import deepcopy
from shutil import rmtree

from cloudify import ctx as ctx_from_imports
from cloudify.exceptions import NonRecoverableError
from cloudify_common_sdk.utils import (
    get_ctx_node,
    get_ctx_instance,
    get_deployment_dir)
from cloudify_common_sdk.processes import general_executor, process_execution

from tg_sdk import Terragrunt, utils as tg_sdk_utils

from .constants import MASKED_ENV_VARS


def configure_ctx(ctx_instance, ctx_node, resource_config=None):
    ctx_from_imports.logger.info('Configuring runtime information...')
    if 'resource_config' not in ctx_instance.runtime_properties:
        ctx_instance.runtime_properties['resource_config'] = \
            resource_config or ctx_node.properties['resource_config']
    validate_resource_config()
    return ctx_instance.runtime_properties['resource_config']


def validate_resource_config():
    ctx_instance = get_ctx_instance()
    ctx_from_imports.logger.info('Validating resource_config...')
    i = 0  # "Error 1" is more readable.
    errors = []
    resource_config = ctx_instance.runtime_properties['resource_config']
    if resource_config['source_path'].startswith('/') and \
            ctx_instance.id not in resource_config['source_path']:
        i += 1
        message = \
            'Error {i} - The source_path provided, {sp}, is invalid. ' \
            'The path should be relative to the source location root.'.format(
                i=i, sp=resource_config['source_path'])
        errors.append(message)
    if isinstance(resource_config['source'], dict) and not \
            resource_config['source'].get('location', '').endswith('.zip') or \
            isinstance(resource_config['source'], str) and not \
            resource_config['source'].endswith('.zip'):
        i += 1
        message = \
            'Error {i} - The source location provided, {s}, is invalid. ' \
            'Only zip archives are currently supported.'.format(
                i=i, s=resource_config['source'])
        errors.append(message)
    if i > 0:
        raise NonRecoverableError(
            'The resource_config provided failed to pass validation: '
            '\n' + '\n'.join(errors))
    ctx_from_imports.logger.info('The provided resource_config is valid.')

# def configure_binary(ni, node_type, prop):
#     path = ni.runtime_properties['resource_config'].get(prop)
#     if path and not os.path.exists(path) or not path:
#         for rel in find_rels_by_node_type(ni, node_type):
#             rp_props = rel.target.instance.runtime_properties
#             path = rp_props['executable_path']
#             if path and not os.path.exists(path):
#                 source = rp_props['resource_config']['installation_source']
#                 tg_dir = os.path.join(
#                       get_deployment_dir(), rel.target.node.id)
#                 install_binary(path, tg_dir, source)
#             if path:
#                 ni.runtime_properties['resource_config'][prop] = path
#
#
# def configure_binaries():
#     ni = get_ctx_instance()
#     configure_binary(ni, 'cloudify.nodes.Terragrunt', 'binary_path')
#     configure_binary(ni, 'cloudify.nodes.terraform', 'terraform_binary_path')


def terragrunt_from_ctx(kwargs):
    _ctx = kwargs.get('ctx')
    ctx_node = get_ctx_node(_ctx)
    ctx_instance = get_ctx_instance(_ctx)
    ctx = _ctx or ctx_from_imports
    configure_ctx(ctx_instance, ctx_node, kwargs.get('resource_config', {}))
    node_instance_dir = get_node_instance_dir()
    # configure_binaries()
    ctx_from_imports.logger.info('Initializing Terragrunt interface...')
    tg = Terragrunt(
        ctx_node.properties,
        logger=ctx.logger,
        executor=run_subprocess,
        cwd=get_node_instance_dir(),
        **ctx_instance.runtime_properties['resource_config']
    )
    update_source = kwargs.get('update_source', False)
    if update_source:
        ctx_from_imports.logger.info(
            'Cleaning up previous Terragrunt workspace...')
        cleanup_old_terragrunt_source()
    if update_source or not tg.source_path or \
            node_instance_dir not in tg.source_path:
        ctx_from_imports.logger.info(
            'Downloading new Terragrunt stack to workspace...')
        download_terragrunt_source(tg.source, node_instance_dir)
        abs_source_path = ''
        if tg.source_path:
            abs_source_path = os.path.join(node_instance_dir, tg.source_path)
        if node_instance_dir not in abs_source_path:
            tg.source_path = node_instance_dir
        else:
            tg.source_path = abs_source_path
        ctx_instance.runtime_properties['resource_config']['source_path'] = \
            tg.source_path
    return tg


def run_subprocess(command,
        logger=None,
        cwd=None,
        env=None,
        additional_args=None,
        return_output=True):
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

    for env_var in MASKED_ENV_VARS:
        if env_var in printed_env:
            printed_env[env_var] = '****'

    printed_args['env'] = printed_env
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


def download_terragrunt_source(source, target):
    """Replace the terraform_source material with a new material.
    This is used in terraform.reload_template operation."""
    ctx_from_imports.logger.info(
        'Using this cloudify.types.terragrunt.SourceSpecification '
        '{source}.'.format(source=source))
    source_tmp_path = tg_sdk_utils.download_source(
        source, target, ctx_from_imports.logger)
    copy_directory(source_tmp_path, target)
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
    run_subprocess(['cp', '-r', os.path.join(src, '*'), dst])


# Merge with TF Plugin
def remove_directory(dir):
    run_subprocess(['rm', '-rf', dir])


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


# Merge with TF all other plugin
def find_rels_by_node_type(node_instance, node_type):
    '''
        Finds all specified relationships of the Cloudify
        instance where the related node type is of a specified type.
    :param `cloudify.context.NodeInstanceContext` node_instance:
        Cloudify node instance.
    :param str node_type: Cloudify node type to search
        node_instance.relationships for.
    :returns: List of Cloudify relationships
    '''
    return [x for x in node_instance.relationships
            if node_type in x.target.node.type_hierarchy]


# Merge with TF Plugin
def download_file(source, destination):
    run_subprocess(['curl', '-o', source, destination])


# Merge with TF Plugin
def install_binary(
        installation_dir,
        executable_path,
        installation_source=None):

    if installation_source:
        download_file(installation_dir, installation_source)
        set_permissions(executable_path)
        os.remove(os.path.join(
            installation_dir, os.path.basename(installation_source)))
    return executable_path


def set_permissions(target_file):
    run_subprocess(
        ['chmod', 'u+x', target_file],
        ctx_from_imports.logger
    )
