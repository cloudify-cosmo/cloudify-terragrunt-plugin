from mock import patch

from . import mock_context
from . import utils
from tg_sdk import Terragrunt

from cloudify.exceptions import NonRecoverableError


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


@patch('cloudify_tg.utils.validate_resource_config')
def test_validate_resource_config(*_):
    node_props = {
        'resource_config': {
            'foo': 'bar'
        }
    }
    instance_props = {
        'foo': 'bar'
    }
    ctx = mock_context('test_validate_resource_config',
                       'test_validate_resource_config',
                       node_props,
                       instance_props)

    ctx.instance.runtime_properties['resource_config'] = {'hello'}

    @patch('cloudify_tg.utils.get_ctx_instance', return_value=ctx)
    def test_bad():
        try:
            utils.validate_resource_config()
            assert False, 'need to raise exception NonRecoverableError'
        except NonRecoverableError:
            assert True, 'except NonRecoverableError exception, Good'

    ctx.instance.runtime_properties['resource_config'] = {'foo': 'bar'}

    @patch('cloudify_tg.utils.get_ctx_instance', return_value=ctx)
    def test_good():
        try:
            utils.validate_resource_config()
            assert True, 'no exceptions'
        except NonRecoverableError:
            assert False, 'except NonRecoverableError exception, Error'


@patch('cloudify_tg.utils.get_ctx_node')
@patch('cloudify_tg.utils.get_ctx_instance')
@patch('cloudify_tg.utils.configure_ctx')
@patch('cloudify_tg.utils.get_node_instance_dir')
@patch('cloudify_tg.utils.Terragrunt')
@patch('cloudify_tg.utils.cleanup_old_terragrunt_source')
@patch('cloudify_tg.utils.download_terragrunt_source')
@patch('cloudify_tg.utils.cleanup_old_terragrunt_source')
def test_terragrunt_from_ctx():
    tg = utils.terragrunt_from_ctx()
    assert isinstance(tg, Terragrunt)

#
# @patch('tg_sdk_utils.download_source')
# @patch('cloudify_tg.utils.copy_directory')
# @patch('cloudify_tg.utils.remove_directory')
# def test_download_terragrunt_source():
#     pass


@patch('cloudify_tg.utils.get_ctx_instance')
@patch('cloudify_tg.utils.get_ctx_node')
def test_get_terragrunt_source_config():
    resalt = utils.get_terragrunt_source_config()
