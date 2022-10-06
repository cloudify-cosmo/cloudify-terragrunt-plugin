from sys import exc_info
from functools import wraps

from .utils import is_using_existing, cleanup_tfvars
from cloudify import utils as cfy_utils
from cloudify.exceptions import NonRecoverableError

from . import utils


def with_terragrunt(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        kwargs['tg'] = utils.terragrunt_from_ctx(kwargs)
        kwargs['tg'].render_inputs()
        try:
            func(*args, **kwargs)
        except Exception as ex:
            _, _, tb = exc_info()
            raise NonRecoverableError(
                "Failed applying",
                causes=[cfy_utils.exception_to_error_cause(ex, tb)])

        if kwargs['tg'].terraform_plan:
            kwargs['ctx'].instance.runtime_properties['terraform_plan'] = \
                kwargs['tg'].terraform_plan

        if kwargs['tg'].terraform_output:
            kwargs['ctx'].instance.runtime_properties['terraform_output'] = \
                kwargs['tg'].terraform_output
        cleanup_tfvars(kwargs)
    return wrapper


def skip_if_existing(func):
    @wraps(func)
    def f(*args, **kwargs):
        if not is_using_existing():
            return func(*args, **kwargs)
    return f
