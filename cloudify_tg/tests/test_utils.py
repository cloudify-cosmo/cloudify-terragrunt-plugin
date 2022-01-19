import os
import tempfile

from mock import patch

from . import mock_context
from .. import utils
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


def test_validate_resource_config():
    properties = {
        'resource_config': {
            'foo': 'bar'
        }
    }
    runtime_properties = {
        'foo': 'bar'
    }
    ctx = mock_context('test_validate_resource_config',
                       'test_validate_resource_config',
                       properties,
                       runtime_properties)

    # ctx.instance.runtime_properties['resource_config'] = {'hello'}

    with patch('cloudify_tg.utils.get_ctx_instance',
               return_value=ctx.instance):
        try:
            utils.validate_resource_config()
            assert False, 'need to raise exception NonRecoverableError'
        except NonRecoverableError:
            assert True, 'except NonRecoverableError exception, Good'

    ctx.instance.runtime_properties['resource_config'] = {
        'foo': 'bar',
        'source_path': '',
        'source': {
            'location': 'foo.zip'
        }
    }

    with patch('cloudify_tg.utils.get_ctx_instance',
               return_value=ctx.instance):
        try:
            utils.validate_resource_config()
            assert True, 'no exceptions'
        except NonRecoverableError as e:
            assert False, '{}'.format(e)

#
# def test_terragrunt_from_ctx():
#     properties = {
#         'resource_config': {
#             'foo': 'bar'
#         }
#     }
#     runtime_properties = {
#         'foo': 'test2',
#         'source_path': '',
#         'resource_config': {
#             'foo': 'bar',
#             'source': {
#                 'location': 'test2.zip'
#             }
#         },
#         'source': {
#             'location': 'test2.zip'
#         }
#     }
#     ctx = mock_context('test_terragrunt_from_ctx',
#                        'test_terragrunt_from_ctx',
#                        properties,
#                        runtime_properties)
#     kwargs = {'ctx': ctx.instance}
#     with patch('cloudify_tg.utils.get_ctx_node', return_value=ctx.instance) \
#          and patch('cloudify_tg.utils.get_ctx_instance',
#                    return_value=ctx.instance) and \
#          patch('cloudify_tg.utils.configure_ctx') and \
#          patch('cloudify_tg.utils.get_node_instance_dir') and \
#          patch('cloudify_tg.utils.Terragrunt') and \
#          patch('cloudify_tg.utils.cleanup_old_terragrunt_source') and \
#          patch('cloudify_tg.utils.download_terragrunt_source') and \
#          patch('cloudify_tg.utils.validate_resource_config') and \
#          patch('cloudify_tg.utils.cleanup_old_terragrunt_source'):
#         tg = utils.terragrunt_from_ctx(kwargs)
#         assert isinstance(tg, Terragrunt)


# def test_download_terragrunt_source():
#     source = 'foobar'
#     target = tempfile.mkdtemp()
#     test_source_tmp_path = tempfile.mkdtemp()
#
#     with patch('cloudify_tg.utils.tg_sdk_utils.download_source',
#                return_value=test_source_tmp_path) and \
#          patch('cloudify_tg.utils.get_node_instance_dir',
#                return_value=test_source_tmp_path):
#
#         utils.download_terragrunt_source(source, target)
#         try:
#             assert not os.path.exists(os.path.basename(test_source_tmp_path))
#         except AssertionError:
#             os.remove(test_source_tmp_path)
#             assert False, '{}'.format(str(AssertionError))
#     assert os.path.basename(test_source_tmp_path) in os.listdir(target),\
#         '{}, {}'.format(
#             os.path.basename(test_source_tmp_path), os.listdir(target))
#
#     os.remove(target)


def test_get_terragrunt_source_config():
    new_source_config = {
        'foo': 'test1',
        'source_path': '',
        'resource_config': {
            'foo': 'bar'
        },
        'source': {
            'location': 'test1.zip'
        }
    }

    properties = {
        'resource_config': {
            'foo': 'bar'
        }
    }
    runtime_properties = {
        'foo': 'test2',
        'source_path': '',
        'resource_config': {
            'foo': 'bar',
            'source': {
                'location': 'test2.zip'
            }
        },
        'source': {
            'location': 'test2.zip'
        }
    }
    ctx = mock_context('test_get_terragrunt_source_config',
                       'test_get_terragrunt_source_config',
                       properties,
                       runtime_properties)

    with patch('cloudify_tg.utils.get_ctx_instance',
               return_vlaue=ctx.instance) and \
         patch('cloudify_tg.utils.get_ctx_node', return_vlaue=ctx.node):

        source = utils.get_terragrunt_source_config()
        assert source == runtime_properties['source']
        source = utils.get_terragrunt_source_config(new_source_config)
        assert source == new_source_config, 'source: {}'.format(source)


def test_cleanup_old_terragrunt_source():
    node_instance_dir = tempfile.mkdtemp()
    try:
        f = open(os.path.join(node_instance_dir, 'readme.txt'), 'w')
        f.close()
    except FileNotFoundError:
        print("The 'docs' directory does not exist")

    assert os.path.exists(node_instance_dir)
    assert len(os.listdir(node_instance_dir)) == 1

    with patch('cloudify_tg.utils.get_node_instance_dir',
               return_value=node_instance_dir):
        utils.cleanup_old_terragrunt_source()

    assert len(os.listdir(node_instance_dir)) == 0
