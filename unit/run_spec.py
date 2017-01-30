from amino.test import Spec
from amino import List, Right, Left, Path, Just, Empty

from kallikrein.run.main import runners, specs_run_task, lookup_loc
from kallikrein.run.line import SpecLine

from unit._fixtures.run.simple import Simple, target_report, EmptySpec


class RunSpec(Spec):

    @property
    def spec_path(self) -> str:
        return 'unit.run_spec.Simple'

    @property
    def file_path(self) -> str:
        base = Path(__file__).parent
        return '{}/_fixtures/run/simple.py'.format(base)

    @property
    def lnum(self) -> int:
        return 34

    @property
    def spec_file_lnum(self) -> List[str]:
        return '{}:{}'.format(self.file_path, self.lnum)

    def file_lnum_loc(self) -> None:
        result = lookup_loc(self.spec_file_lnum)
        assert isinstance(result, Right)
        locs = result.value
        assert len(locs) == 1
        loc = locs[0]
        assert loc.mod == 'unit._fixtures.run.simple'
        assert loc.cls == Simple
        assert loc.meth == Just('simple')

    def file_loc(self) -> None:
        result = lookup_loc(self.file_path)
        assert isinstance(result, Right)
        locs = result.value
        assert len(locs) == 2
        loc_e = locs[0]
        assert loc_e.mod == 'unit._fixtures.run.simple'
        assert loc_e.cls == EmptySpec
        assert loc_e.meth == Empty()
        loc_s = locs[1]
        assert loc_s.cls == Simple
        assert loc_s.meth == Empty()

    def method_loc(self) -> None:
        result = lookup_loc('{}.simple'.format(self.spec_path))
        assert isinstance(result, Right)
        locs = result.value
        assert len(locs) == 1
        loc = locs[0]
        assert loc.cls == Simple
        assert loc.meth == Just('simple')

    def runners(self) -> None:
        result = runners(List(self.spec_path))
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
        self._run(List(self.spec_path))

    def run_file_lnum(self) -> None:
        self._run(List(self.spec_file_lnum))

    def run_file(self) -> None:
        self._run(List(self.file_path))

    def no_docstring(self) -> None:
        result = specs_run_task(List('unit.run_spec.EmptySpec'))
        assert isinstance(result.attempt, Left)


__all__ = ('RunSpec',)
