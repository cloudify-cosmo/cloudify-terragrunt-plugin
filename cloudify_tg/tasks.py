from cloudify.decorators import operation

from .utils import with_terragrunt

@operation
@with_terragrunt
def precreate(tg, **_):
    tg.terragrunt_info()
    tg.graph_dependencies()
    tg.validate_inputs()
    tg.plan()


@operation
@with_terragrunt
def create(tg, **_):
    tg.apply()


@operation
@with_terragrunt
def poststart(tg, **_):
    tg.outputs()


@operation
@with_terragrunt
def delete(tg, **_):
    tg.destroy()
