from sys import exit

from golgi import Config, cli

from kallikrein.run.main import kallikrein_run


@cli(positional=(('specs', '*'),))
def klk() -> None:
    specs = Config['run'].specs
    if not kallikrein_run(specs):
        exit(1)

__all__ = ('klk',)
