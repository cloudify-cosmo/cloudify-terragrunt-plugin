
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
                'AWS_ACCESS_KEY_ID': '**',
                'AWS_SECRET_ACCESS_KEY': '**',
                'AWS_DEFAULT_REGION': 'eu-west-1'
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
    # terragrunt.terragrunt_info()
