import logging

from .. import utils


def test_get_logger():
    assert isinstance(utils.get_logger(), logging.Logger)


def test_basic_executor():
    output = utils.basic_executor('echo hello world')
    assert output == 'hello world'
    assert output != 'hello worlds'
    try:
        utils.basic_executor('foo bar')
    except FileNotFoundError:
        pass
    else:
        raise RuntimeError('Executing "foo bar" succeeded.')


def test_get_version_string():
    assert utils.get_version_string('v2.1.3') == '2.1.3'
    assert utils.get_version_string('v2.1') == '2.1'
    assert utils.get_version_string('1.2.3v') == '1.2.3'


def test_yield_file():
    content = 'data'
    with utils.yield_file(content) as yielded:
        f = open(yielded, 'r')
        f.seek(0)
        assert 'data' in f.read()
