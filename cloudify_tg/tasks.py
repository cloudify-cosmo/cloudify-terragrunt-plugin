from cloudify.decorators import operation

from . import utils, decorators

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
    tg.outputs()


@operation
@decorators.with_terragrunt
def delete(tg, **_):
    tg.destroy()


def update_terragrunt_source(new_source):
    utils.cleanup_old_terragrunt_source()
    utils.download_terragrunt_source(new_source)
