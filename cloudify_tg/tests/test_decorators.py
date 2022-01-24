from cloudify.exceptions import NonRecoverableError

from .. import decorators
from . import mock_context, mock_terragrunt_from_ctx


@decorators.with_terragrunt
def fake_function(*args, **kwargs):

    for item in args:
        if isinstance(item, Exception):
            raise Exception('caught ya')

    return args, kwargs


def test_decorator_raises():
    args = [Exception('foo')]
    kwargs = {
        'ctx': mock_context('test_decorator_raises',
                            'test_decorator_raises',
                            {'foo': 'bar'},
                            {'baz': 'taco'})
    }
    with mock_terragrunt_from_ctx():
        try:
            fake_function(*args, **kwargs)
        except Exception as e:
            if not isinstance(e, NonRecoverableError):
                raise RuntimeError(
                    'The wrong type of exception was raised: {}'.format(
                        str(e)))
            if not ('Failed applying' in str(e)):
                raise RuntimeError(
                    'The wrong exception message was printed, {}'.format(e))
        else:
            raise RuntimeError('Test test_decorator_raises failed. '
                               'Did not raise expected exception.')


def test_decorator_stores_runtime_props():
    args = []
    kwargs = {
        'ctx': mock_context('test_decorator_raises',
                            'test_decorator_raises',
                            {'foo': 'bar'},
                            {'baz': 'taco'})
    }
    with mock_terragrunt_from_ctx():
        fake_function(*args, **kwargs)
        assert kwargs['ctx'].instance.runtime_properties[
                   'terraform_plan'] == 'terraform_plan'
        assert kwargs['ctx'].instance.runtime_properties[
                   'terraform_output'] == 'terraform_output'
