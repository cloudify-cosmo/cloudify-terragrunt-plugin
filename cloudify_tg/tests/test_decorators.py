from mock import patch, Mock
from contextlib import contextmanager

from cloudify.mocks import MockCloudifyContext
from cloudify.exceptions import NonRecoverableError

from .. import decorators


def mock_context(test_name,
                 test_node_id,
                 test_properties,
                 test_runtime_properties):

    ctx = MockCloudifyContext(
        node_id=test_node_id,
        properties=test_properties,
        runtime_properties=None if not test_runtime_properties
        else test_runtime_properties,
        deployment_id=test_name
    )
    return ctx


@decorators.with_terragrunt
def fake_function(*args, **kwargs):

    for item in args:
        if isinstance(item, Exception):
            raise Exception('caught ya')

    return args, kwargs


@contextmanager
def mock_terragrunt_from_ctx(*_, **__):
    with patch('cloudify_tg.decorators.utils') as mocked:
        mocked.terragrunt_from_ctx.return_value = Mock()
        yield mocked


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


def test_decorator_stores():
    args = []
    kwargs = {
        'ctx': mock_context('test_decorator_raises',
                            'test_decorator_raises',
                            {'foo': 'bar'},
                            {'baz': 'taco'})
    }
    with mock_terragrunt_from_ctx() as mocked:
        mocked.terraform_plan = 'terraform_plan'
        mocked.terraform_output = 'terraform_output'
        fake_function(*args, **kwargs)
        assert kwargs['ctx'].instance.runtime_properties[
                   'terraform_plan'] == 'terraform_plan'
        assert kwargs['ctx'].instance.runtime_properties[
                   'terraform_output'] == 'terraform_output'
