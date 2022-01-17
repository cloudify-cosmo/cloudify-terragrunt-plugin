from mock import patch, Mock
from contextlib import contextmanager

from cloudify.mocks import MockCloudifyContext

from .. import utils


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


@contextmanager
def mock_terragrunt_from_ctx(*_, **__):
    with patch('cloudify_tg.decorators.utils') as mocked:
        mocked.terragrunt_from_ctx.return_value = Mock(
            terraform_plan='terraform_plan',
            terraform_output='terraform_output')
        yield mocked


# def configure_ctx(ctx_instance, ctx_node, resource_config=None):
@patch('cloudify_tg.utils.get_ctx_instance')
@patch('cloudify_tg.utils.get_ctx_node')
def test_configure_ctx(self, *_):
    ctx = mock_context('test_configure_ctx',
                       'test_configure_ctx',
                       {},
                       {})

