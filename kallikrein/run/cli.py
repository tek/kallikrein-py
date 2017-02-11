from sys import exit

from golgi import Config, cli

from kallikrein.run.main import kallikrein_run_lazy


@cli(positional=(('specs', '*'),))
def klk() -> None:
    specs = Config['run'].specs
    if not kallikrein_run_lazy(specs):
        exit(1)

__all__ = ('klk',)
