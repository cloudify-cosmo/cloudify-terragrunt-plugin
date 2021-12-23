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
