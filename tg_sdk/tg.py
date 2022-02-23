import os
import re
import json

from . import utils
from cloudify.exceptions import NonRecoverableError
from cloudify_common_sdk.utils import v1_gteq_v2


class Terragrunt(object):

    def __init__(self,
                 properties,
                 logger=None,
                 executor=None,
                 masked_env_vars=None,
                 *args,
                 **kwargs):
        self._properties = properties
        self._logger = logger
        self._additional_args = args
        self._additional_kwargs = kwargs
        self._resource_config = None
        self._source = kwargs.get('source')
        self._source_path = None
        self._binary_path = kwargs.get('binary_path')
        self._terraform_binary_path = kwargs.get('terraform_binary_path')
        self._command_options = {}
        self.executor = executor or utils.basic_executor
        self.cwd = kwargs.get('cwd')
        self._terraform_plan = None
        self._terraform_output = []
        self._run_all = None
        self.masked_env_vars = masked_env_vars

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
        if os.path.exists(value):
            self._source_path = value
            props = self.properties.get('resource_config', {})
            props['source_path'] = value

    @property
    def binary_path(self):
        """The local path on the manager to the Terragrunt binary
        root directory.

        :return: str
        """
        if not self._binary_path:
            self._binary_path = self.resource_config.get('binary_path')
        return self._binary_path

    @binary_path.setter
    def binary_path(self, value):
        self._binary_path = value

    @property
    def terraform_binary_path(self):
        if not self._terraform_binary_path:
            self._terraform_binary_path = \
                self.resource_config.get('terraform_binary_path')

        version_output = \
            self._execute([self._terraform_binary_path, '--version'])

        version = utils.get_version_string(version_output)
        if v1_gteq_v2('1.0.0', version):
            raise NonRecoverableError(
             'Cloudify Terragrunt plugin requires that the Terraform binary in'
             ' use be above version 1.0.0.')
        self.logger.info('terraform_path: {p}, version: {v}'
                         .format(p=self._terraform_binary_path, v=version))
        return self._terraform_binary_path

    @terraform_binary_path.setter
    def terraform_binary_path(self, value):
        self._terraform_binary_path = value

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

    def _execute(self, command, return_output=True):
        args = [command]
        kwargs = {'logger': self.logger}
        if self.cwd:
            kwargs['cwd'] = self.cwd
        if self.environment_variables:
            kwargs['additional_env'] = self.environment_variables
        if self.masked_env_vars:
            kwargs['masked_env_vars'] = self.masked_env_vars
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
        new_result = re.sub('}\s*{', '}____TG_PLUGIN_PLAN____{', result)
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
        self.logger.debug(self._terraform_plan)
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
