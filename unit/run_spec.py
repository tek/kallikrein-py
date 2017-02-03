from amino.test import Spec
from amino import List, Right, Left, Path, Just, Empty, __, _

from kallikrein.run.main import runners, specs_run_task, lookup_loc
from kallikrein.run.line import SpecLine
from kallikrein.expectation import MultiExpectationResult

from unit._fixtures.run.simple import (Simple, target_report, EmptySpec,
                                       target_report_method)
from unit._fixtures.run.unsafe import target_report_unsafe
from unit._fixtures.run.exception import target_report_exception


class RunSpec(Spec):

    @property
    def spec_path(self) -> str:
        return 'unit.run_spec.Simple'

    @property
    def spec_path_method(self) -> str:
        return '{}.{}'.format(self.spec_path, 'simple')

    def _file_path(self, name: str) -> str:
        base = Path(__file__).parent
        return '{}/_fixtures/run/{}.py'.format(base, name)

    @property
    def simple_path(self) -> str:
        return self._file_path('simple')

    @property
    def lnum(self) -> int:
        return 37

    @property
    def lnum_class(self) -> int:
        return 24

    @property
    def spec_file_lnum(self) -> List[str]:
        return '{}:{}'.format(self.simple_path, self.lnum)

    @property
    def spec_file_lnum_class(self) -> List[str]:
        return '{}:{}'.format(self.simple_path, self.lnum_class)

    def file_lnum_loc(self) -> None:
        result = lookup_loc(self.spec_file_lnum)
        assert isinstance(result, Right)
        locs = result.value
        assert len(locs) == 1
        loc = locs[0]
        assert loc.mod == 'unit._fixtures.run.simple'
        assert loc.cls == Simple
        assert loc.meth == Just('simple')

    def file_lnum_loc_class(self) -> None:
        result = lookup_loc(self.spec_file_lnum_class)
        assert isinstance(result, Right)
        locs = result.value
        assert len(locs) == 1
        loc = locs[0]
        assert loc.mod == 'unit._fixtures.run.simple'
        assert loc.cls == Simple
        assert loc.meth == Empty()

    def file_loc(self) -> None:
        result = lookup_loc(self.simple_path)
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
        report = result.value.report
        assert report == target_report

    def _run_method(self, spec: str) -> None:
        task = specs_run_task(List(spec))
        result = task.attempt
        assert isinstance(result, Right)
        report = result.value.report
        assert report == target_report_method

    def run_path(self) -> None:
        self._run(List(self.spec_path))

    def run_file_path_method(self) -> None:
        self._run_method(self.spec_path_method)

    def run_file_lnum_method(self) -> None:
        self._run_method(self.spec_file_lnum)

    def run_file_lnum_class(self) -> None:
        self._run(List(self.spec_file_lnum_class))

    def run_file(self) -> None:
        self._run(List(self.simple_path))

    def run_unsafe(self) -> None:
        task = specs_run_task(List(self._file_path('unsafe')))
        result = task.attempt
        assert isinstance(result, Right)
        report = result.value.report
        assert report == target_report_unsafe

    def run_exception(self) -> None:
        task = specs_run_task(List(self._file_path('exception')))
        result = task.attempt
        assert isinstance(result, Right)
        report = result.value.report
        assert report == target_report_exception

    def run_multi(self) -> None:
        task = specs_run_task(List(self._file_path('multi')))
        result = task.attempt
        assert isinstance(result, Right)
        exp_m = result.value.specs.head // __.results.lift(1) / _.result
        assert exp_m.present
        exp = exp_m.x
        assert isinstance(exp, MultiExpectationResult)

    def no_docstring(self) -> None:
        result = specs_run_task(List('unit.run_spec.EmptySpec'))
        assert isinstance(result.attempt, Left)


__all__ = ('RunSpec',)
