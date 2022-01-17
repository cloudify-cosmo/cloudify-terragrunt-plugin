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
        tg.terragrunt_from_ctx().graph_dependencies.assert_called_once()
        tg.terragrunt_from_ctx().validate_inputs.assert_called_once()
        tg.terragrunt_from_ctx().plan.assert_called_once()
        assert 'terraform_plan' in ctx.instance.runtime_properties


def test_create():
    ctx = mock_context('test_create',
                       'test_create',
                       {},
                       {})
    with mock_terragrunt_from_ctx() as tg:
        tasks.create(ctx=ctx)
        tg.terragrunt_from_ctx().apply.assert_called_once()
        assert 'terraform_plan' in ctx.instance.runtime_properties


def test_poststart():
    ctx = mock_context('test_poststart',
                       'test_poststart',
                       {},
                       {})
    with mock_terragrunt_from_ctx() as tg:
        tasks.poststart(ctx=ctx)
        tg.terragrunt_from_ctx().output.assert_called_once()
        assert 'terraform_plan' in ctx.instance.runtime_properties


def test_delete():
    ctx = mock_context('test_delete',
                       'test_delete',
                       {},
                       {})
    with mock_terragrunt_from_ctx() as tg:
        tasks.delete(ctx=ctx)
        tg.terragrunt_from_ctx().destroy.assert_called_once()
        assert 'terraform_plan' in ctx.instance.runtime_properties


def test_terragrunt_plan():
    ctx = mock_context('test_terragrunt_plan',
                       'test_terragrunt_plan',
                       {},
                       {})
    with mock_terragrunt_from_ctx() as tg:
        tasks.terragrunt_plan(ctx=ctx)
        tg.terragrunt_from_ctx().plan.assert_called_once()
        assert 'terraform_plan' in ctx.instance.runtime_properties


def test_terragrunt_destroy():
    ctx = mock_context('test_terragrunt_destroy',
                       'test_terragrunt_destroy',
                       {},
                       {})
    with mock_terragrunt_from_ctx() as tg:
        tasks.terragrunt_destroy(ctx=ctx)
        tg.terragrunt_from_ctx().destroy.assert_called_once()
        assert 'terraform_plan' in ctx.instance.runtime_properties


def test_terragrunt_output():
    ctx = mock_context('test_terragrunt_output',
                       'test_terragrunt_output',
                       {},
                       {})
    with mock_terragrunt_from_ctx() as tg:
        tasks.terragrunt_output(ctx=ctx)
        tg.terragrunt_from_ctx().output.assert_called_once()
        assert 'terraform_plan' in ctx.instance.runtime_properties


def test_terragrunt_apply():
    ctx = mock_context('test_terragrunt_apply',
                       'test_terragrunt_apply',
                       {},
                       {})
    with mock_terragrunt_from_ctx() as tg:
        tasks.terragrunt_apply(ctx=ctx)
        tg.terragrunt_from_ctx().apply.assert_called_once()
        assert 'terraform_plan' in ctx.instance.runtime_properties


def test_terragrunt_info():
    ctx = mock_context('test_terragrunt_info',
                       'test_terragrunt_info',
                       {},
                       {})
    with mock_terragrunt_from_ctx() as tg:
        tasks.terragrunt_info(ctx=ctx)
        tg.terragrunt_from_ctx().terragrunt_info.assert_called_once()
        assert 'terraform_plan' in ctx.instance.runtime_properties


def test_validate_inputs():
    ctx = mock_context('test_validate_inputs',
                       'test_validate_inputs',
                       {},
                       {})
    with mock_terragrunt_from_ctx() as tg:
        tasks.validate_inputs(ctx=ctx)
        tg.terragrunt_from_ctx().validate_inputs.assert_called_once()
        assert 'terraform_plan' in ctx.instance.runtime_properties


def test_graph_dependencies():
    ctx = mock_context('test_graph_dependencies',
                       'test_graph_dependencies',
                       {},
                       {})
    with mock_terragrunt_from_ctx() as tg:
        tasks.graph_dependencies(ctx=ctx)
        tg.terragrunt_from_ctx().graph_dependencies.assert_called_once()
        assert 'terraform_plan' in ctx.instance.runtime_properties


def test_render_json():
    ctx = mock_context('test_render_json',
                       'test_render_json',
                       {},
                       {})
    with mock_terragrunt_from_ctx() as tg:
        tasks.render_json(ctx=ctx)
        tg.terragrunt_from_ctx().render_json.assert_called_once()
        assert 'terraform_plan' in ctx.instance.runtime_properties


def test_run_command():
    command = 'graph-dependencies'
    ctx = mock_context('test_run_command',
                       'test_run_command',
                       {},
                       {})
    with mock_terragrunt_from_ctx() as tg:
        tasks.run_command(command=command, ctx=ctx)
        tg.terragrunt_from_ctx().update_command_options.assert_called_once()
        tg.terragrunt_from_ctx().execute.assert_called_once()
        assert tg._command_options != {}
        assert 'terraform_plan' in ctx.instance.runtime_properties
