
from tg_sdk import tg

init_params = {
    'properties': {}
}

if __name__ == '__main__':
    terragrunt = tg.Terragrunt(**init_params)
    terragrunt.terragrunt_info()

