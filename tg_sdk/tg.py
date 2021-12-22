import os
from contextlib import contextmanager

from . import utils


class Terragrunt(object):

    def __init__(self,
                 properties,
                 logger=None,
                 executor=None,
                 *args,
                 **kwargs):
        self._properties = properties
        self._logger = logger
        self._additional_args = args
        self._additional_kwargs = kwargs
        self._resource_config = None
        self._source = None
        self._source_path = None
        self._binary_path = None
        self.executor = executor or utils.basic_executor
        self.cwd = kwargs.get('cwd')

    @property
    def properties(self):
        return self._properties

    @property
    def logger(self):
        return self._logger or utils.get_logger('TerragruntLogger')

    @property
    def resource_config(self):
        if not self._resource_config:
            props = self.properties.get('resource_config', {})
            kwargs = self._additional_kwargs.get('resource_config', {})
            if isinstance(kwargs, dict):
                props.update(kwargs)
            self._resource_config = props
        return self._resource_config

    @property
    def source(self):
        """The local path or remote URL where to find the Terragrunt Stack.
        :return: str
        """
        if not self._source:
            self._source = self.resource_config.get('source')
        return self._source

    @property
    def source_path(self):
        """The local path on the manager to the expanded Terragrunt Stack
        root directory.

        :return: str
        """
        if not self._source_path:
            source_path = self.resource_config.get('source_path')
            if os.path.exists(source_path):
                self._source_path = source_path
            elif os.path.exists(os.path.join(self.cwd, source_path)):
                self._source_path = os.path.join(self.cwd, source_path)
        return self._source_path

    @property
    def binary_path(self):
        """The local path on the manager to the Terragrunt binary
        root directory.

        :return: str
        """
        return self.resource_config.get('binary_path')

    @property
    def terraform_binary_path(self):
        return self.resource_config.get('terraform_binary_path')

    @property
    def run_all(self):
        """ True or False, whether to execute as run_all.
        :return: bool
        """
        return self.resource_config.get('run_all', False)

    @property
    def environment_variables(self):
        """ A dictionary of key values to export to env.

        :return: dict
        """
        return self.resource_config.get('environment_variables', {})

    @property
    def command_options(self):
        return self.resource_config.get('command_options', {})

    @property
    def version(self):
        return utils.get_version_string(
            self._execute([self.binary_path, '--version']))

    def _execute(self, command):
        args = [command]
        kwargs = {'logger': self.logger}
        if self.cwd:
            kwargs['cwd'] = self.cwd
        if self.environment_variables:
            kwargs['env'] = self.environment_variables
        return self.executor(*args, **kwargs)

    def execute(self, name):
        command = [self.binary_path, name]
        if self.run_all:
            command.insert(1, 'run-all')
        command.extend(self.command_options.get('all', []))
        command.extend(self.command_options.get(name, []))
        if 'terragrunt-tfpath' not in command and self.terraform_binary_path:
            command.extend(['--terragrunt-tfpath', self.terraform_binary_path])
        self._execute(command)

    def plan(self):
        return self.execute('plan')

    def apply(self):
        return self.execute('apply')

    def destroy(self):
        return self.execute('destroy')

    def output(self):
        return self.execute('output')

    def terragrunt_info(self):
        return self.execute('terragrunt-info')

    def validate_inputs(self):
        return self.execute('validate-inputs')

    def graph_dependencies(self):
        return self.execute('graph-dependencies')

    def render_json(self):
        return self.execute('render-json')

    @contextmanager
    def update_source_path(self, update_source=False):
        if update_source or not self.source_path:
            source_path = os.path.join(
                self.cwd, self.resource_config.get('source_path'))
            try:
                yield self.source
            finally:
                self._source_path = source_path

