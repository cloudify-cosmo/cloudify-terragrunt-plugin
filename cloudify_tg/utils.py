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
        executor=run,
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


def run(command,
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
            if node_type in x.type_hierarchy]


# Merge with TF Plugin
def download_file(source, destination):
    run(['curl', '-o', source, destination])


# Merge with TF Plugin
def install_binary(
        installation_dir,
        executable_path,
        installation_source=None):

    if installation_source:
        download_file(installation_dir, installation_source)
        set_permissions(executable_path)
    return executable_path


def set_permissions(target_file):
    run(
        ['chmod', 'u+x', target_file],
        ctx_from_imports.logger
    )


def get_executable_path():
    """The Terragrunt binary executable.
    It should either be: null, in which case it defaults to
    /opt/manager/resources/deployments/{tenant}/{deployment_id}/terragrunt
    or it will be /usr/bin/terragrunt, and this should be used as an
    existing resource.
    Any other value will probably not work for the user.
    """
    instance = get_instance()
    executable_path = instance.runtime_properties.get('executable_path')
    if not executable_path:
        terragrunt_config = get_terragrunt_config()
        executable_path = terragrunt_config.get('executable_path')
    if not executable_path:
        executable_path = \
            os.path.join(get_node_instance_dir(), 'terragrunt')
    if not os.path.exists(executable_path) and \
            is_using_existing():
        node = get_node()
        terragrunt_config = node.properties.get('terragrunt_config', {})
        executable_path = terragrunt_config.get('executable_path')
    instance.runtime_properties['executable_path'] = executable_path
    return executable_path


def get_instance(_ctx=None, target=False, source=False):
    """Get a CTX instance, either NI, target or source."""
    _ctx = _ctx or ctx_from_imports
    if _ctx.type == RELATIONSHIP_INSTANCE:
        if target:
            return _ctx.target.instance
        elif source:
            return _ctx.source.instance
        return _ctx.source.instance
    else:  # _ctx.type == NODE_INSTANCE
        return _ctx.instance


def get_terragrunt_config(target=False):
    """get the cloudify.nodes.terragrunt or cloudify.nodes.terragrunt.Module
    terragrunt_config"""
    instance = get_instance(target=target)
    terragrunt_config = instance.runtime_properties.get('terragrunt_config')
    if terragrunt_config:
        return terragrunt_config
    node = get_node(target=target)
    return node.properties.get('terragrunt_config', {})


def get_node(_ctx=None, target=False):
    """Get a node ctx"""
    _ctx = _ctx or ctx_from_imports
    if _ctx.type == RELATIONSHIP_INSTANCE:
        if target:
            return _ctx.target.node
        return _ctx.source.node
    else:  # _ctx.type == NODE_INSTANCE
        return _ctx.node


def is_using_existing(target=True):
    """Decide if we need to do this work or not."""
    resource_config = get_resource_config(target=target)
    if not target:
        tf_rel = find_terragrunt_node_from_rel()
        if tf_rel:
            resource_config = tf_rel.target.instance.runtime_properties.get(
                'resource_config', {})
    return resource_config.get('use_existing_resource', True)


def get_resource_config(target=False):
    """Get the cloudify.nodes.terragrunt.Module resource_config"""
    instance = get_instance(target=target)
    resource_config = instance.runtime_properties.get('resource_config')
    if not resource_config or ctx_from_imports.workflow_id == 'install':
        node = get_node(target=target)
        resource_config = node.properties.get('resource_config', {})
    return resource_config


def find_terragrunt_node_from_rel():
    return find_rel_by_type(
        ctx_from_imports.instance, 'cloudify.terragrunt.relationships.run_on_host')


def find_rel_by_type(node_instance, rel_type):
    rels = find_rels_by_type(node_instance, rel_type)
    return rels[0] if len(rels) > 0 else None


def find_rels_by_type(node_instance, rel_type):
    return [x for x in node_instance.relationships
            if rel_type in x.type_hierarchy]


def get_installation_source(target=False):
    """This is the URL or file where we can get the Terragrunt binary"""
    resource_config = get_resource_config(target=target)
    source = resource_config.get('installation_source')
    if not source:
        raise NonRecoverableError(
            'No download URL for terragrunt binary executable file was '
            'provided and use_external_resource is False. '
            'Please provide a valid download URL.')
    return source
