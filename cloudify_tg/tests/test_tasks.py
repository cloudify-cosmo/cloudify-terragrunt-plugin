from mock import patch, Mock
from contextlib import contextmanager

from cloudify.mocks import MockCloudifyContext


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


@patch('cloudify_tg.tasks.terragrunt_info')
@patch('cloudify_tg.tasks.graph_dependencies')
@patch('cloudify_tg.tasks.validate_inputs')
# @patch('cloudify_tg.tasks.plan')
def test_precreate(self, *_):
    with mock_terragrunt_from_ctx() as tg:
        tg.terragrunt_info()
        tg.graph_dependencies()
        tg.validate_inputs()
