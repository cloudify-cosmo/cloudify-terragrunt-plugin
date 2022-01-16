from mock import patch, Mock
from contextlib import contextmanager

from cloudify.mocks import MockCloudifyContext

from .. import tasks

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


def test_precreate():
    ctx = mock_context('test_precreate',
                       'test_precreate',
                       {},
                       {})
    with mock_terragrunt_from_ctx() as tg:
        tasks.precreate(ctx=ctx)
        tg.terragrunt_from_ctx().terragrunt_info.assert_called_once()
        assert 'terraform_plan' in ctx.instance.runtime_properties


