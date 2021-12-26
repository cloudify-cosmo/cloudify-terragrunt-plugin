from cloudify.decorators import operation

from . import decorators


@operation
@decorators.with_terragrunt
def precreate(tg, **_):
    tg.terragrunt_info()
    tg.graph_dependencies()
    tg.validate_inputs()
    tg.plan()


@operation
@decorators.with_terragrunt
def create(tg, **_):
    tg.apply()


@operation
@decorators.with_terragrunt
def poststart(tg, **_):
    tg.output()


@operation
@decorators.with_terragrunt
def delete(tg, **_):
    tg.destroy()


@operation
@decorators.with_terragrunt
def terragrunt_plan(tg, **_):
    tg.plan()


@operation
@decorators.with_terragrunt
def terragrunt_destroy(tg, **_):
    tg.destroy()

@operation
@decorators.with_terragrunt
def terragrunt_output(tg, **_):
    tg.terraform_output()

@operation
@decorators.with_terragrunt
def terragrunt_apply(tg, **_):
    tg.apply()


@operation
@decorators.with_terragrunt
def terragrunt_info(tg, **_):
    tg.terragrunt_info()


@operation
@decorators.with_terragrunt
def validate_inputs(tg, **_):
    tg.validate_inputs()


@operation
@decorators.with_terragrunt
def graph_dependencies(tg, **_):
    tg.graph_dependencies()


@operation
@decorators.with_terragrunt
def render_json(tg, **_):
    tg.render_json()

@operation
@decorators.with_terragrunt
def run_command(command, command_options, tg, *args, **kwargs):
    tg.update_command_options({command: command_options})
    tg.execute(command)
