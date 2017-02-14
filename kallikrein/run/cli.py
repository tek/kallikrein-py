from golgi import Config, cli

from amino import _

from kallikrein.run.main import kallikrein_run_lazy


@cli(positional=(('specs', '*'),))
def klk() -> int:
    specs = Config['run'].specs
    return 0 if kallikrein_run_lazy(specs).exists(_.success) else 1

__all__ = ('klk',)
