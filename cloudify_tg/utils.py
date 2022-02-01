import os
from shutil import rmtree

from cloudify import ctx as ctx_from_imports
from cloudify.exceptions import NonRecoverableError
from cloudify_common_sdk.utils import (
    get_ctx_node,
    run_subprocess,
    copy_directory,
    find_rel_by_type,
    get_ctx_instance,
    remove_directory,
    get_node_instance_dir,
    find_rels_by_node_type
)
from cloudify_common_sdk.resource_downloader import get_shared_resource

from tg_sdk import Terragrunt

try:
    from cloudify.constants import RELATIONSHIP_INSTANCE, NODE_INSTANCE
except ImportError:
    NODE_INSTANCE = 'node-instance'
    RELATIONSHIP_INSTANCE = 'relationship-instance'


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


def configure_ctx(ctx_instance, ctx_node, resource_config=None):
    ctx_from_imports.logger.info('Configuring runtime information...')
    if 'resource_config' not in ctx_instance.runtime_properties:
        ctx_instance.runtime_properties['resource_config'] = \
            resource_config or ctx_node.properties['resource_config']
    update_terraform_binary(ctx_instance)
    update_terragrunt_binary(ctx_instance)
    validate_resource_config()
    return ctx_instance.runtime_properties['resource_config']


def update_terragrunt_binary(ctx_instance):
    tg_nodes = find_rels_by_node_type(
        ctx_instance, 'cloudify.nodes.terragrunt')
    if len(tg_nodes) == 1:
        ctx_instance.runtime_properties['resource_config']['binary_path'] = \
            tg_nodes[0].target.instance.runtime_properties['executable_path']
    elif not len(tg_nodes):
        return
    else:
        raise NonRecoverableError(
            'Only one relationship of type '
            'cloudify.relationships.terragrunt.depends_on '
            'to node type cloudify.nodes.terragrunt may be used per node.')


def update_terraform_binary(ctx_instance):
    tg_nodes = find_rels_by_node_type(
        ctx_instance, 'cloudify.nodes.terraform')
    if len(tg_nodes) == 1:
        ctx_instance.runtime_properties['resource_config']['terraform_'
                                                           'binary_path'] = \
            tg_nodes[0].target.instance.runtime_properties['executable_path']
    elif not len(tg_nodes):
        return
    else:
        raise NonRecoverableError(
            'Only one relationship of type '
            'cloudify.relationships.terraform.depends_on '
            'to node type cloudify.nodes.terraform may be used per node.')


def validate_resource_config():
    ctx_instance = get_ctx_instance()
    ctx_from_imports.logger.info('Validating resource_config...')
    i = 0  # "Error 1" is more readable.
    errors = []
    if 'resource_config' not in ctx_instance.runtime_properties:
        raise NonRecoverableError(
            'Error {i} - No resource_config was provided, {sp}, is invalid. '
            .format(i=i, sp=ctx_instance.runtime_properties))

    resource_config = ctx_instance.runtime_properties['resource_config']
    if 'source_path' not in resource_config:
        i += 1
        message = \
            'Error {i} - No source path was provided, {sp}, is invalid. '\
            .format(i=i, sp=resource_config['source_path'])
        errors.append(message)
    else:
        if resource_config['source_path'].startswith('/') and \
                ctx_instance.id not in resource_config['source_path']:
            i += 1
            message = \
                'Error {i} - The source_path provided, {sp}. ' \
                'The path should be relative to the source location root.'\
                .format(i=i, sp=resource_config['source_path'])
            errors.append(message)
    if 'source' not in resource_config:
        i += 1
        message = \
            'Error {i} - No source was provided, {sp}. '\
            .format(i=i, sp=resource_config['source_path'])
        errors.append(message)
    else:
        if isinstance(resource_config['source'], dict) and not \
                resource_config['source'].get('location', '').endswith('.zip')\
                or isinstance(resource_config['source'], str) and not \
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
    path_to_rm = os.path.dirname(source_tmp_path)
    remove_directory(path_to_rm)


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


def is_using_existing():
    """Decide if we need to do this work or not."""
    resource_config = get_resource_config()
    return resource_config.get('use_existing_resource', True)


def find_terragrunt_node_from_rel():
    return find_rel_by_type(
        ctx_from_imports.instance,
        'cloudify.terragrunt.relationships.run_on_host')


def get_property(property_name, ctx_node=None, ctx_instance=None):
    ctx_node = ctx_node or ctx_from_imports.node
    ctx_instance = ctx_instance or ctx_from_imports.instance
    from_props = ctx_node.properties.get(property_name)
    from_runtime_props = ctx_instance.runtime_properties.get(property_name)
    if from_runtime_props:
        return from_runtime_props
    return from_props


def get_terragrunt_config():
    return get_property('terragrunt_config')


def get_resource_config():
    return get_property('resource_config')
