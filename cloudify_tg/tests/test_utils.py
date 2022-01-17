from mock import patch


from .. import utils
from . import mock_context, mock_terragrunt_from_ctx


# def configure_ctx(ctx_instance, ctx_node, resource_config=None):
@patch('cloudify_tg.utils.validate_resource_config')
def test_configure_ctx(*_):
    node_props = {
        'resource_config': {
            'foo': 'bar'
        }
    }
    instance_props = {
        'foo': 'bar'
    }
    ctx = mock_context('test_configure_ctx',
                       'test_configure_ctx',
                       node_props,
                       instance_props)
    result = utils.configure_ctx(ctx.instance, ctx.node)
    assert ctx.instance.runtime_properties == {
        'foo': 'bar',
        'resource_config': {
            'foo': 'bar'
        }
    }
    assert result == ctx.instance.runtime_properties['resource_config']
