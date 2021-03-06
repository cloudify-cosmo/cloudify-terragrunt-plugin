import os
from tg_sdk import tg

init_params = {
    'properties': {
        'resource_config': {
            'binary_path': '/usr/local/bin/terragrunt',
            'terraform_binary_path': '/usr/local/bin/terraform',
            'source': 'https://github.com/Nelynehemia/terragrunt/archive/refs/heads/main.zip',
            'source_path': '',
            'variables': {},
            'environment_variables': {
                'AWS_ACCESS_KEY_ID': os.environ['AWS_ACCESS_KEY_ID'],
                'AWS_SECRET_ACCESS_KEY': os.environ['AWS_SECRET_ACCESS_KEY'],
                'AWS_DEFAULT_REGION': os.environ['AWS_DEFAULT_REGION']
            },
            'run_all': False,
            'command_options': {
                'all': ['--terragrunt-non-interactive', '--terragrunt-log-level', 'debug'],
                'apply': ['-auto-approve'],
                'destroy': ['-auto-approve'],
                'plan': ['-json'],
                'output': ['-json']
            }
        }
    }
}

if __name__ == '__main__':
    terragrunt = tg.Terragrunt(**init_params)
    # terragrunt.terraform_output()
    # terragrunt.terragrunt_info()
    # terragrunt.validate_inputs()
    # terragrunt.graph_dependencies()
    # terragrunt.render_json()
    #
    # terragrunt.terraform_plan()
    # terragrunt.apply()
    # terragrunt.destroy()
    # terragrunt.output()
