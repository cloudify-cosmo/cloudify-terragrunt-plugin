from mock import patch


from .. import utils
from . import mock_context, mock_terragrunt_from_ctx
from cloudify.exceptions import NonRecoverableError

node_props = {
        'resource_config': {
            'foo': 'bar'
        }
}
instance_props = {
        'foo': 'bar'
}
ctx = mock_context('test',
                   'test',
                   node_props,
                   instance_props)


@patch('cloudify_tg.utils.validate_resource_config')
def test_configure_ctx(*_):

    result = utils.configure_ctx(ctx.instance, ctx.node)
    assert ctx.instance.runtime_properties == {
        'foo': 'bar',
        'resource_config': {
            'foo': 'bar'
        }
    }
    assert result == ctx.instance.runtime_properties['resource_config']


@patch('cloudify_tg.utils.validate_resource_config')
@patch('cloudify_tg.utils.get_ctx_instance', return_value=ctx)
def test_validate_resource_config(*_):
    ctx_test1 = utils.configure_ctx(ctx.instance, ctx.node)
    ctx_test1.runtime_properties['resource_config'] = "abcd"

    try:
        utils.validate_resource_config()
    except NonRecoverableError:
        assert 'test_validate_resource_config'


@patch('cloudify_tg.utils.get_ctx_node')
@patch('cloudify_tg.utils.get_ctx_instance')
@patch('cloudify_tg.utils.configure_ctx')
@patch('cloudify_tg.utils.get_node_instance_dir')
@patch('cloudify_tg.utils.Terragrunt')
@patch('cloudify_tg.utils.cleanup_old_terragrunt_source')
@patch('cloudify_tg.utils.download_terragrunt_source')
@patch('cloudify_tg.utils.cleanup_old_terragrunt_source')
def test_terragrunt_from_ctx():
    print()
