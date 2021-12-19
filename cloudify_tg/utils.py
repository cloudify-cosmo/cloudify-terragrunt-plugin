import os
import sys
from copy import deepcopy
from functools import wraps

from cloudify import ctx as ctx_from_imports
from cloudify_common_sdk import (
    get_ctx_node,
    get_ctx_instance,
    get_deployment_dir)
from cloudify.exceptions import NonRecoverableError
from cloudify.utils import exception_to_error_cause
from cloudify_common_sdk.processes import general_executor, process_execution

from tg_sdk import Terragrunt


# SHOULD_BE_USER_PROVIDED
MASKED_ENV_VARS = {}


def with_terragrunt(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        ctx = kwargs.get('ctx') or ctx_from_imports
        kwargs['tg'] = terragrunt_from_ctx(ctx)
        try:
            func(*args, **kwargs)
        except Exception as ex:
            _, _, tb = sys.exc_info()
            raise NonRecoverableError(
                "Failed applying",
                causes=[exception_to_error_cause(ex, tb)])
    return wrapper


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


# Merge with TF Plugin
def mkdir_p(path):
    import pathlib
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)
