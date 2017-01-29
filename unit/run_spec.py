from amino.test import Spec
from amino import List, Right, Left

from kallikrein.run.main import runners, specs_run_task
from kallikrein.run.line import SpecLine

from unit._fixtures.run.simple import Simple, target_report


class RunSpec(Spec):

    @property
    def specs(self) -> List[str]:
        return List('unit.run_spec.Simple')

    def runners(self) -> None:
        result = runners(self.specs)
        assert isinstance(result, Right)
        assert len(result.value) == 1
        runner = result.value[0]
        assert runner.spec_cls == Simple
        lines = runner.lines
        assert len(lines) == 9
        assert len(lines.filter_type(SpecLine)) == 3

    def run(self) -> None:
        task = specs_run_task(self.specs)
        result = task.attempt
        assert isinstance(result, Right)
        assert result.value.report == target_report

    def no_docstring(self) -> None:
        result = specs_run_task(List('unit.run_spec.Empty'))
        assert isinstance(result.attempt, Left)


__all__ = ('RunSpec',)
