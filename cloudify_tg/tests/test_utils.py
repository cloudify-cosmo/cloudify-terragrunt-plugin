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


@patch('cloudify_tg.utils.get_ctx_node')
@patch('cloudify_tg.utils.get_ctx_instance')
@patch('cloudify_tg.utils.get_node_instance_dir')
@patch('cloudify_tg.utils.configure_ctx')
@patch('cloudify_tg.utils.download_terragrunt_source')
def test_terragrunt_from_ctx(mock_ctx_node,
                             mock_ctx_instance,
                             mock_node_instance_dir, *_):
    node_instance_dir = tempfile.mkdtemp()
    mock_node_instance_dir.return_value = node_instance_dir
    properties = {
        'resource_config': {
            'foo': 'bar',
            'source': {
                'location': 'foo',
            },
            'source_path': 'bar',
        }
    }
    runtime_properties = {
        'foo': 'test2',
        'resource_config': {
            'foo': 'bar',
            'source': {
                'location': 'foo',
            },
            'source_path': 'bar',
        }
    }
    ctx = mock_context('test_terragrunt_from_ctx',
                       'test_terragrunt_from_ctx',
                       properties,
                       runtime_properties)
    kwargs = {'ctx': ctx}
    mock_ctx_node.return_value = ctx.node
    mock_ctx_instance.return_value = ctx.instance
    tg = utils.terragrunt_from_ctx(kwargs)
    assert isinstance(tg, Terragrunt)
    assert ctx.instance.runtime_properties == runtime_properties, \
        '{}'.format(ctx.instance.runtime_properties)
    # assert tg.source_path == 'bar', '{}'.format(tg.source_path)
    # TODO assert tg.source_path == 'WHATEVER RIGHT VALUE IS'
    os.removedirs(node_instance_dir)


@patch('cloudify_tg.utils.copy_directory')
@patch('cloudify_tg.utils.remove_directory')
@patch('cloudify_tg.utils.download_source')
@patch('cloudify_common_sdk.utils.get_node_instance_dir')
def test_download_terragrunt_source(mock_cp, mock_rm, *_):
    source = 'foobar'
    target = tempfile.mkdtemp()
    test_source_tmp_path = tempfile.mkdtemp()
    try:
        utils.download_terragrunt_source(source, target)
        assert mock_cp.called_once_with(test_source_tmp_path, target)
        assert mock_rm.called_once_with(test_source_tmp_path)
    finally:
        os.rmdir(test_source_tmp_path)
        os.rmdir(target)


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
