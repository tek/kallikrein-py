from amino.test import Spec
from amino import List, Right, Left, Path, Just, Empty, __, _, Maybe
from amino.list import Lists
from amino.task import TaskException

from kallikrein.run.main import (runners, specs_run_task, lookup_loc,
                                 specs_run_task_lazy, convert_lazy_result)
from kallikrein.run.line import SpecLine
from kallikrein.expectation import (MultiExpectationResult,
                                    PendingExpectationResult,
                                    SingleExpectationResult)
from kallikrein.run.data import SpecLocation
from kallikrein.match_result import MatchResult

from unit._fixtures.run.simple import (Simple, target_report, EmptySpec,
                                       target_report_method)
from unit._fixtures.run.unsafe import target_report_unsafe
from unit._fixtures.run.exception import target_report_exception
from unit._fixtures.run.pending import PendingSpec
from unit._fixtures.run.all_specs import AllSpecsSpec


def _spec_path(cls: type) -> str:
    mod = cls.__module__
    name = cls.__name__
    return '{}.{}'.format(mod, name)

spec_mod = Simple.__module__
meth_name = Simple.simple.__name__
spec_path_parts = Lists.split(spec_mod, '.')

spec_cls_name = Simple.__name__
empty_cls_name = EmptySpec.__name__

spec_cls_path = spec_path_parts.cat(spec_cls_name).join_dot
spec_method_path = '{}.{}'.format(spec_cls_path, 'simple')
empty_cls_path = spec_path_parts.cat(empty_cls_name).join_dot
empty_method_path = '{}.{}'.format(empty_cls_path, 'specific')

lnum = 39
lnum_class = 26


def _file_path(name: str) -> str:
    base = Path(__file__).parent
    return '{}/_fixtures/run/{}.py'.format(base, name)


simple_file_path = _file_path('simple')
spec_file_lnum = '{}:{}'.format(simple_file_path, lnum)
spec_file_lnum_class = '{}:{}'.format(simple_file_path, lnum_class)
spec_file_lnum_file = '{}:1'.format(simple_file_path)


def _lookup(spec: str, count: int=1, meth: Maybe=Empty()) -> SpecLocation:
    result = lookup_loc(spec)
    assert isinstance(result, Right)
    locs = result.value
    assert len(locs) == count
    loc = locs[-1]
    assert loc.mod == spec_mod
    assert loc.cls == Simple
    assert loc.meth == meth
    return locs


class RunSpec(Spec):

    def file_lnum_loc(self) -> None:
        _lookup(spec_file_lnum, meth=Just('simple'))

    def file_lnum_loc_class(self) -> None:
        _lookup(spec_file_lnum_class)

    def file_loc(self) -> None:
        locs = _lookup(simple_file_path, count=2)
        loc_e = locs[0]
        assert loc_e.mod == spec_mod
        assert loc_e.cls == EmptySpec
        assert loc_e.meth == Empty()

    def file_lnum_loc_file(self) -> None:
        _lookup(spec_file_lnum_file, count=2)

    def file_loc_class(self) -> None:
        _lookup('{}:{}'.format(simple_file_path, spec_cls_name))

    # TODO
    # def dir_loc(self) -> None:
    #     _lookup(dir_path)

    def path_mod(self) -> None:
        _lookup(spec_mod, count=2)

    # TODO
    # def path_package(self) -> None:
    #     _lookup(spec_pkg)

    def path_class(self) -> None:
        _lookup(spec_cls_path)

    def path_class_method(self) -> None:
        _lookup('{}.simple'.format(spec_cls_path), meth=Just(meth_name))

    def runners(self) -> None:
        result = runners(List(spec_cls_path))
        assert isinstance(result, Right)
        assert len(result.value) == 1
        runner = result.value[0]
        assert runner.spec_cls == Simple
        lines = runner.lines
        assert len(lines) == 9
        assert len(lines.filter_type(SpecLine)) == 3

    def _run(self, specs: List[str]) -> MatchResult:
        task = specs_run_task(specs)
        result = task.attempt
        assert isinstance(result, Right)
        return result.value

    def _run_simple(self, specs: List[str]) -> None:
        result = self._run(specs)
        report = result.report
        assert report == target_report

    def _run_method(self, spec: str) -> None:
        task = specs_run_task(List(spec))
        result = task.attempt
        assert isinstance(result, Right)
        report = result.value.report
        assert report == target_report_method

    def run_path(self) -> None:
        self._run_simple(List(spec_cls_path))

    def run_file_path_method(self) -> None:
        self._run_method(spec_method_path)

    def run_file_lnum_method(self) -> None:
        self._run_method(spec_file_lnum)

    def run_file_lnum_class(self) -> None:
        self._run_simple(List(spec_file_lnum_class))

    def run_file(self) -> None:
        self._run_simple(List(simple_file_path))

    def run_unsafe(self) -> None:
        task = specs_run_task(List(_file_path('unsafe')))
        result = task.attempt
        assert isinstance(result, Right)
        report = result.value.report
        assert report == target_report_unsafe

    def run_exception(self) -> None:
        task = specs_run_task(List(_file_path('exception')))
        result = task.attempt
        assert isinstance(result, Right)
        report = result.value.report
        assert report == target_report_exception

    def run_multi(self) -> None:
        task = specs_run_task(List(_file_path('multi')))
        result = task.attempt
        assert isinstance(result, Right)
        exp_m = result.value.specs.head // __.results.lift(1) / _.result
        assert exp_m.present
        exp = exp_m.x
        assert isinstance(exp, MultiExpectationResult)

    def no_docstring(self) -> None:
        task = specs_run_task(List(empty_cls_path))
        result = task.attempt
        assert isinstance(result, Left)
        value = result.value
        assert isinstance(value, TaskException)
        err = SpecLocation.no_docstring_msg.format(empty_cls_name)
        assert str(value.cause) == err

    def no_docstring_specific(self) -> None:
        task = specs_run_task(List(empty_method_path))
        result = task.attempt
        assert result.present

    def pending_spec(self) -> None:
        task = specs_run_task(List(_spec_path(PendingSpec)))
        result = task.attempt
        assert result.present
        value = result.value.specs.head / _.results
        pending = value // __.lift(1) / _.result
        assert pending.present
        assert isinstance(pending.x, PendingExpectationResult)
        active = value // __.lift(2) / _.result
        assert active.present
        assert isinstance(active.x, SingleExpectationResult)

    def all_specs(self) -> None:
        task = specs_run_task(List(_spec_path(AllSpecsSpec)))
        result = task.attempt
        assert result.present
        assert len(result.value.report_lines) == 3

    def stream(self) -> None:
        e = specs_run_task_lazy(List(spec_cls_path))
        assert e.present
        results = e.value
        spec_result = convert_lazy_result(results, False)
        assert spec_result.report == target_report


__all__ = ('RunSpec',)
