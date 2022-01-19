import os
from shutil import rmtree

from cloudify import ctx as ctx_from_imports
from cloudify.exceptions import NonRecoverableError
from cloudify_common_sdk.utils import (
    mkdir_p,
    get_ctx_node,
    download_file,
    run_subprocess,
    copy_directory,
    set_permissions,
    get_ctx_instance,
    get_deployment_dir
)
from cloudify_common_sdk.processes import general_executor, process_execution, get_shared_resource
    remove_directory,
    get_deployment_dir,
    get_node_instance_dir,
)

from tg_sdk import Terragrunt


def download_source(source, target_directory, logger):
    logger.debug('Downloading {source} to {dest}.'.format(
        source=source, dest=target_directory))
    if isinstance(source, dict):
        source_tmp_path = get_shared_resource(
            source, dir=target_directory,
            username=source.get('username'),
            password=source.get('password'))
    else:
        source_tmp_path = get_shared_resource(
            source, dir=target_directory)
    logger.debug('Downloaded temporary source path {}'.format(source_tmp_path))
    # Plugins must delete this.
    return source_tmp_path

from .constants import MASKED_ENV_VARS

try:
    from cloudify.constants import RELATIONSHIP_INSTANCE, NODE_INSTANCE
except ImportError:
    NODE_INSTANCE = 'node-instance'
    RELATIONSHIP_INSTANCE = 'relationship-instance'


def configure_ctx(ctx_instance, ctx_node, resource_config=None):
    ctx_from_imports.logger.info('Configuring runtime information...')
    if 'resource_config' not in ctx_instance.runtime_properties:
        ctx_instance.runtime_properties['resource_config'] = \
            resource_config or ctx_node.properties['resource_config']
    update_terragrunt_binary(ctx_instance)
    validate_resource_config()
    return ctx_instance.runtime_properties['resource_config']


def update_terragrunt_binary(ctx_instance):
    terragrunt_nodes = find_rels_by_node_type(ctx_instance,
                                              'cloudify.nodes.terragrunt')
    if len(terragrunt_nodes) == 1:
        ctx_instance.runtime_properties['resource_config']['binary_path'] = \
            terragrunt_nodes[0].instance.runtime_properties['executable_path']
    elif not len(terragrunt_nodes):
        return
    else:
        raise NonRecoverableError(
            'Only one relationship of type '
            'cloudify.relationships.terragrunt.depends_on '
            'to node type cloudify.nodes.terragrunt may be used per node.')


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


def download_terragrunt_source(source, target):
    """Replace the terraform_source material with a new material.
    This is used in terraform.reload_template operation."""
    ctx_from_imports.logger.info(
        'Using this cloudify.types.terragrunt.SourceSpecification '
        '{source}.'.format(source=source))
    source_tmp_path = download_source(
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
