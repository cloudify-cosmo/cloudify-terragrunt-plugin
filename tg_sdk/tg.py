import os
import json
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
        self._command_options = {}
        self.executor = executor or utils.basic_executor
        self.cwd = kwargs.get('cwd')
        self._terraform_plan = None
        self._terraform_output = []
        self._run_all = None

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
        return self._source_path

    @source_path.setter
    def source_path(self, value):
        """The local path on the manager to the expanded Terragrunt Stack
        root directory.

        :return: str
        """
        self._resource_config['source_path'] = value
        self._source_path = value

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
        if not self._run_all:
            self._run_all = self.resource_config.get('run_all', False)
        return self._run_all

    @run_all.setter
    def run_all(self, value):
        self._run_all = value

    @property
    def environment_variables(self):
        """ A dictionary of key values to export to env.

        :return: dict
        """
        return self.resource_config.get('environment_variables', {})

    @property
    def command_options(self):
        if self._command_options:
            return self._command_options
        return self.resource_config.get('command_options', {})

    def update_command_options(self, new_dict):
        self._command_options.update(new_dict)

    @property
    def version(self):
        return utils.get_version_string(
            self._execute([self.binary_path, '--version']))

    def _execute(self, command, return_output):
        args = [command]
        kwargs = {'logger': self.logger}
        if self.cwd:
            kwargs['cwd'] = self.cwd
        if self.environment_variables:
            kwargs['additional_env'] = self.environment_variables
        kwargs['return_output'] = return_output
        return self.executor(*args, **kwargs)

    def execute(self, name, return_output=True):
        command = [self.binary_path, name]
        if self.run_all:
            command.insert(1, 'run-all')
        command.extend(self.command_options.get('all', []))
        command.extend(self.command_options.get(name, []))
        if 'terragrunt-tfpath' not in command and self.terraform_binary_path:
            command.extend(['--terragrunt-tfpath', self.terraform_binary_path])
        return self._execute(command, return_output)

    def plan(self):
        plan = {
            'resource_drifts': [],
            'outputs': [],
            'change_summary': {}
        }
        result = self.execute('plan', return_output=False)
        new_result = result.replace('}{', '}____TG_PLUGIN_PLAN____{')
        for item in new_result.split('____TG_PLUGIN_PLAN____'):
            rendered = json.loads(item)
            if 'type' not in rendered:
                continue
            elif rendered['type'] == 'outputs':
                plan['outputs'] = rendered['outputs']
            elif rendered['type'] == 'resource_drift':
                plan['resource_drifts'].append(rendered['change'])
            elif rendered['type'] == 'change_summary':
                plan['change_summary'] = rendered['changes']

        self._terraform_plan = plan
        return self.terraform_plan

    @property
    def terraform_plan(self):
        self.logger.info(self._terraform_plan)
        return self._terraform_plan

    def apply(self):
        return self.execute('apply')

    def destroy(self):
        return self.execute('destroy')

    def output(self):
        result = self.execute('output', return_output=False)
        self._terraform_output = json.loads(result)
        return self.terraform_output

    @property
    def terraform_output(self):
        return self._terraform_output

    def terragrunt_info(self):
        return self.execute('terragrunt-info')

    def validate_inputs(self):
        return self.execute('validate-inputs')

    def graph_dependencies(self):
        return self.execute('graph-dependencies')

    def render_json(self):
        return self.execute('render-json')
