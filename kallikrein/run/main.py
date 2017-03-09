from typing import Any, Callable
from datetime import datetime

from hues import huestr

from golgi import Config

from amino import List, Either, Task, Right, curried, L, _, Maybe, __, Try
from amino.regex import Regex
from amino.logging import amino_root_logger
from amino.task import TaskException

from kallikrein.run.line import (Line, SpecLine, PlainLine, ResultLine,
                                 FatalLine)
from kallikrein.run.data import SpecLocation, SpecResult, SpecsResult
from kallikrein.run.lookup_loc import lookup_loc
from kallikrein.expectation import (Expectation, unsafe_expectation_result,
                                    ExpectationResult, FailedUnsafeSpec,
                                    FatalSpec)
from kallikrein.expectable import ExpectationFailed


class SpecRunner:

    def __init__(self, location: SpecLocation, lines: List[Line]) -> None:
        self.location = location
        self.lines = lines

    @property
    def valid_lines(self) -> List[Line]:
        return (
            self.location.meth /
            __.exclude_by_name /
            self.lines.filter_not |
            self.lines
        )

    @property
    def spec_cls(self) -> type:
        return self.location.cls

    def _run_line(self, line: Line) -> Task[Line]:
        return (
            Task.now(line)
            if isinstance(line, PlainLine) else
            self.run_spec(line)
            if isinstance(line, SpecLine) else
            Task.failed('invalid line in spec: {}'.format(line))
        )

    @property
    def run(self) -> Task[List[Line]]:
        return self.valid_lines.traverse(self._run_line, Task)

    @property
    def run_lazy(self) -> List[Task[Line]]:
        return self.valid_lines / self._run_line

    @property
    def unsafe(self) -> bool:
        return hasattr(self.spec_cls, '__unsafe__')

    def run_spec(self, line: SpecLine) -> Task[ResultLine]:
        def recover(error: TaskException) -> Expectation:
            cause = error.cause
            return (
                FailedUnsafeSpec(line.name, cause)
                if isinstance(cause, ExpectationFailed) else
                FatalSpec(line.name, cause)
            )
        def execute(spec: Callable[[Any], Expectation],
                    inst: Any) -> Task[Expectation]:
            return Try(spec, inst).right_or_map(recover)
        def evaluate(expectation: Expectation) -> Task[ExpectationResult]:
            err = 'spec "{}" did not return an Expectation, but `{}`'
            return (
                expectation.evaluate
                if isinstance(expectation, Expectation) else
                Task.now(unsafe_expectation_result)
                if self.unsafe else
                Task.failed(err.format(line.text, expectation)))
        def run(inst: Any) -> Task[ResultLine]:
            def teardown(a: ExpectationResult) -> None:
                if hasattr(inst, 'teardown'):
                    inst.teardown()
            if hasattr(inst, 'setup'):
                inst.setup()
            start = datetime.now()
            def result(r: ExpectationResult) -> ResultLine:
                return ResultLine(line.text, inst, r, datetime.now() - start)
            return (
                Task.delay(execute, line.spec, inst) //
                evaluate %
                teardown /
                result
            )
        return Task.delay(self.spec_cls) // run

    def __str__(self) -> str:
        return '{}({}, {})'.format(self.__class__.__name__, self.spec_cls,
                                   self.lines)


def parse_locator(loc: str) -> Either[str, List[SpecLocation]]:
    return lookup_loc(loc)


def collect_specs(specs: List[str]) -> Either[str, List[SpecLocation]]:
    return specs.traverse(parse_locator, Either) / _.join


def spec_line(spec: SpecLocation, attr: str, line: str) -> Maybe[SpecLine]:
    err = 'spec class `{}` does not define a spec `{}`'
    return (
        Maybe.getattr(spec.cls, attr)
        .to_either(err.format(spec.cls, attr))
        .map(L(SpecLine)(attr, line, _))
    )


spec_regex = r'\s*(?P<text>[^\$]+)\$(?P<spec>\w+)'


@curried
def parse_line(spec: Any, line: str) -> Line:
    match = Regex(spec_regex).match(line)
    match_data = lambda m: m.group('spec') & m.group('text')
    return (
        (match // match_data)
        .map2(L(spec_line)(spec, _, _)) |
        Right(PlainLine(line))
    )


def construct_runner(loc: SpecLocation) -> Either[str, SpecRunner]:
    doc = loc.doc.o(Right('')) if loc.allow_empty else loc.doc
    return (
        doc /
        List.lines //
        __.traverse(parse_line(loc), Either) /
        L(SpecRunner)(loc, _)
    )


def construct_runners(specs: List[SpecLocation]
                      ) -> Either[str, List[SpecRunner]]:
    return specs.traverse(construct_runner, Either)


def run_spec_class(runner: SpecRunner) -> Task[List[SpecResult]]:
    return runner.run / SpecResult


def run_specs(runners: List[SpecRunner]) -> Task[SpecsResult]:
    return runners.traverse(run_spec_class, Task) / SpecsResult


def run_specs_lazy(runners: List[SpecRunner]
                   ) -> List[List[Task[Line]]]:
    return runners.map(_.run_lazy)


def runners(specs: List[str]) -> Either[str, List[SpecRunner]]:
    return (
        collect_specs(specs) //
        construct_runners
    )


def specs_run_task(specs: List[str]) -> Task[SpecsResult]:
    return runners(specs).task() // run_specs


def specs_run_task_lazy(specs: List[str]
                        ) -> Either[str, List[List[Task[Line]]]]:
    return runners(specs) / run_specs_lazy


def convert_lazy_result(result: List[List[Line]], log: bool=False
                        ) -> SpecsResult:
    def convert_spec(spec: Task[ExpectationResult]) -> Line:
        line = spec.attempt.right_or_map(FatalLine)
        if log:
            line.print_report()
        return line
    def convert_loc(loc: List[Task[ExpectationResult]]) -> SpecsResult:
        return SpecResult(loc / convert_spec)
    result = SpecsResult(result / convert_loc)
    if log:
        result.print_stats()
    return result


def run_error(e: Any) -> None:
    msg = e.cause if isinstance(e, TaskException) else e
    if Config['general'].debug:
        amino_root_logger.caught_exception('running spec', msg)
    else:
        amino_root_logger.error('error in spec run:')
        amino_root_logger.error(huestr(str(msg)).red.bold.colorized)


def kallikrein_run(specs: List[str]) -> Either[Exception, SpecsResult]:
    return (
        (specs_run_task(specs) % __.print_report())
        .attempt
        .leffect(run_error)
    )


def kallikrein_run_lazy(specs: List[str]) -> Either[Exception, SpecsResult]:
    return (
        specs_run_task_lazy(specs) /
        L(convert_lazy_result)(_, True)
    ).leffect(run_error)

__all__ = ('kallikrein_run',)
