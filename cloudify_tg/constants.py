SUPPORTED_TG_COMMANDS = [
    'run-all',
    'plan',
    'apply',
    'output',
    'destroy',
    'validate',
    'terragrunt-info',
    'validate-inputs',
    'graph-dependencies',
    'hclfmt',
    'aws-provider-patch',
    'render-json'
]

SUPPORTED_TG_COMMANDS_OPTIONS = [
    '--terragrunt-config',
    '--terragrunt-tfpath',
    '--terragrunt-no-auto-init',
    '--terragrunt-no-auto-retry',
    '--terragrunt-non-interactive',
    '--terragrunt-working-dir',
    '--terragrunt-download-dir',
    '--terragrunt-source',
    '--terragrunt-source-map',
    '--terragrunt-source-update',
    '--terragrunt-ignore-dependency-errors',
    '--terragrunt-iam-role',
    '--terragrunt-iam-assume-role-duration',
    '--terragrunt-iam-assume-role-session-name',
    '--terragrunt-exclude-dir',
    '--terragrunt-include-dir',
    '--terragrunt-strict-include',
    '--terragrunt-strict-validate',
    '--terragrunt-ignore-dependency-order',
    '--terragrunt-ignore-external-dependencies',
    '--terragrunt-include-external-dependencies',
    '--terragrunt-parallelism',
    '--terragrunt-debug',
    '--terragrunt-log-level',
    '--terragrunt-check',
    '--terragrunt-hclfmt-file',
    '--terragrunt-override-attr',
    '--terragrunt-json-out',
    '--terragrunt-modules-that-include',
    'debug',
    '-auto-approve',
    '-json'
]

# SHOULD_BE_USER_PROVIDED
MASKED_ENV_VARS = {
    'AWS_SECRET_ACCESS_KEY',
    'AWS_ACCESS_KEY_ID',
    'AWS_DEFAULT_REGION'
}
