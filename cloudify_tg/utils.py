import os
from shutil import rmtree

from cloudify import ctx as ctx_from_imports
from cloudify.exceptions import NonRecoverableError
from cloudify_common_sdk.utils import (
    get_ctx_node,
    run_subprocess,
    copy_directory,
    get_ctx_instance,
    remove_directory,
    get_node_instance_dir,
)

from tg_sdk import Terragrunt, utils as tg_sdk_utils


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
