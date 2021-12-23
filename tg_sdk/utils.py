import re
import logging
from contextlib import contextmanager
from tempfile import NamedTemporaryFile
from subprocess import check_output, CalledProcessError

from cloudify_common_sdk.resource_downloader import get_shared_resource


def get_logger(logger_name=None):
    logger_name = logger_name or 'tg_sdk_logger'
    return logging.getLogger(logger_name)


def basic_executor(command, *args, **kwargs):
    if isinstance(command, str):
        command = command.split(' ')
    if 'logger' in kwargs:
        kwargs.pop('logger')

    try:
        result = check_output(command, *args, **kwargs)
    except CalledProcessError as e:
        result = str(e)
    if isinstance(result, bytes):
        return result.decode('utf-8').strip()
    return result.strip()


def dump_hcl(data, file_obj):
    hcl_data = translate_hcl(data)
    file_obj.write(hcl_data)


def translate_hcl(data):
    pass


def get_version_string(output):
    result = re.search(r'([\d.]+)', output)
    if result:
        return result.group(1)


def download_source(source, target_directory, logger):
    logger.debug('Downloading {source} to {dest}.'.format(
        source=source, dest=target_directory))
    if isinstance(source, dict):
        source_tmp_path = get_shared_resource(
            source, dir=target_directory,
            username=source.get('username'),
            password=source.get('password'))
    else:
        source_tmp_path = get_shared_resource(
            source, dir=target_directory)
    logger.debug('Downloaded temporary source path {}'.format(source_tmp_path))
    # Plugins must delete this.
    return source_tmp_path


@contextmanager
def yield_file(content):
    with NamedTemporaryFile() as f:
        f.write(content)
        f.flush()
        yield f.name
