from mock import Mock, patch
from contextlib import contextmanager

from cloudify.state import current_ctx
from cloudify.mocks import MockCloudifyContext, MockNodeInstanceContext


class MockNodeInstanceTerragruntContext(MockNodeInstanceContext):

    def __init__(self, *args, **kwargs):
        self._type = None
        super(MockNodeInstanceTerragruntContext, self).__init__(
            *args, **kwargs)

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, value):
        self._type = value


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
    ctx._instance = MockNodeInstanceTerragruntContext(
        ctx._instance.id,
        ctx._instance.runtime_properties,
        ctx._instance.relationships,
        ctx._instance.index
    )
    ctx._instance.type = 'node-instance'
    current_ctx.set(ctx=ctx)
    return ctx


@contextmanager
def mock_terragrunt_from_ctx(*_, **__):
    with patch('cloudify_tg.decorators.utils') as mocked:
        mocked.terragrunt_from_ctx.return_value = Mock(
            terraform_plan='terraform_plan',
            terraform_output='terraform_output')
        yield mocked
