from typing import Any

from amino import (List, Either, Task, Right, curried, L, _, Maybe, __)
from amino.regex import Regex
from amino.logging import amino_root_logger
from amino.task import TaskException

from kallikrein.run.line import Line, SpecLine, PlainLine, ResultLine
from kallikrein.run.data import SpecLocation, SpecResult, SpecsResult
from kallikrein.run.lookup_loc import lookup_loc


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

    @property
    def run(self) -> Task[Line]:
        def run(line: Line) -> Task[Line]:
            return (
                Task.now(line)
                if isinstance(line, PlainLine) else
                self.run_spec(line)
                if isinstance(line, SpecLine) else
                Task.failed('invalid line in spec: {}'.format(line))
            )
        return self.lines.traverse(run, Task)

    def run_spec(self, line: SpecLine) -> Task[ResultLine]:
        def run(inst: Any) -> Task[ResultLine]:
            inst.setup()
            return (
                Task.delay(line.spec, inst) /
                L(ResultLine)(line.text, inst, _)
            )
        return Task.delay(self.spec_cls) // run

    def __str__(self) -> str:
        return '{}({}, {})'.format(self.__class__.__name__, self.spec_cls,
                                   self.lines)


def parse_locator(loc: str) -> Either[str, SpecLocation]:
    return lookup_loc(loc).o(SpecLocation.from_path(loc))


def collect_specs(specs: List[str]) -> Either[str, List[SpecLocation]]:
    return specs.traverse(parse_locator, Either)


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
    return (
        loc.doc /
        List.lines //
        __.traverse(parse_line(loc), Either) /
        L(SpecRunner)(loc, _)
    )


def construct_runners(specs: List[Any]) -> Either[str, List[SpecRunner]]:
    return specs.traverse(construct_runner, Either)


def run_spec_class(runner: SpecRunner) -> Task[List[SpecResult]]:
    return runner.run / SpecResult


def run_specs(runners: List[SpecRunner]) -> Task[SpecsResult]:
    return runners.traverse(run_spec_class, Task) / SpecsResult


def runners(specs: List[str]) -> Either[str, List[SpecRunner]]:
    return (
        collect_specs(specs) //
        construct_runners
    )


def specs_run_task(specs: List[str]) -> Task[SpecsResult]:
    return runners(specs).task() // run_specs


def kallikrein_run(specs: List[str]) -> Either[Exception, SpecsResult]:
    def error(e: Any) -> None:
        msg = e.cause if isinstance(e, TaskException) else e
        amino_root_logger.error(msg)
    return (specs_run_task(specs) % __.print_report()).attempt.leffect(error)

__all__ = ('kallikrein_run',)
