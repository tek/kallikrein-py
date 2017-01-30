from amino.test import Spec
from amino import List, Right, Left, Path, Just

from kallikrein.run.main import runners, specs_run_task, lookup_file_loc
from kallikrein.run.line import SpecLine

from unit._fixtures.run.simple import Simple, target_report


class RunSpec(Spec):

    @property
    def specs_path(self) -> List[str]:
        return List('unit.run_spec.Simple')

    @property
    def spec_file(self) -> List[str]:
        base = Path(__file__).parent
        spec = '{}/_fixtures/run/simple.py:34'.format(base)
        return spec

    def file_loc(self) -> None:
        result = lookup_file_loc(self.spec_file)
        assert isinstance(result, Right)
        loc = result.value
        assert loc.mod == 'unit._fixtures.run.simple'
        assert loc.cls == Simple
        assert loc.meth == Just('simple')

    def runners(self) -> None:
        result = runners(self.specs_path)
        assert isinstance(result, Right)
        assert len(result.value) == 1
        runner = result.value[0]
        assert runner.spec_cls == Simple
        lines = runner.lines
        assert len(lines) == 9
        assert len(lines.filter_type(SpecLine)) == 3

    def _run(self, specs: List[str]) -> None:
        task = specs_run_task(specs)
        result = task.attempt
        assert isinstance(result, Right)
        assert result.value.report == target_report

    def run_path(self) -> None:
        self._run(self.specs_path)

    def run_file(self) -> None:
        self._run(List(self.spec_file))

    def no_docstring(self) -> None:
        result = specs_run_task(List('unit.run_spec.EmptySpec'))
        assert isinstance(result.attempt, Left)


__all__ = ('RunSpec',)
