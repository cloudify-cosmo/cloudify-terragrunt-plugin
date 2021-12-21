import sys
from functools import wraps

from cloudify import ctx as ctx_from_imports
from cloudify.exceptions import NonRecoverableError
from cloudify.utils import exception_to_error_cause

from . import utils


def with_terragrunt(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        ctx = kwargs.get('ctx') or ctx_from_imports
        tg = utils.terragrunt_from_ctx(ctx)
        kwargs['tg'] = tg
        try:
            func(*args, **kwargs)
        except Exception as ex:
            _, _, tb = sys.exc_info()
            raise NonRecoverableError(
                "Failed applying",
                causes=[exception_to_error_cause(ex, tb)])
    return wrapper