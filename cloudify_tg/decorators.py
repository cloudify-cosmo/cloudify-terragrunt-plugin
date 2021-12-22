from sys import exc_info
from functools import wraps

from cloudify import utils as cfy_utils
from cloudify.exceptions import NonRecoverableError

from . import utils


def with_terragrunt(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        kwargs['tg'] = utils.terragrunt_from_ctx(kwargs)
        try:
            func(*args, **kwargs)
        except Exception as ex:
            _, _, tb = exc_info()
            raise NonRecoverableError(
                "Failed applying",
                causes=[cfy_utils.exception_to_error_cause(ex, tb)])
    return wrapper
