from typing import Any

from amino import List, Either, Task, Right, curried, L, _, Maybe, __
from amino.regex import Regex
from amino.logging import Logging, amino_root_logger
from amino.task import TaskException

from kallikrein.run.line import Line, SpecLine, PlainLine, ResultLine
from kallikrein.match_result import MatchResult


class SpecRunner:

    def __init__(self, spec_cls: type, lines: List[Line]) -> None:
        self.spec_cls = spec_cls
        self.lines = lines

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


class SpecResult(Logging):

    def __init__(self, results: List[MatchResult]) -> None:
        self.results = results

    @property
    def report_lines(self) -> List[str]:
        return self.results // _.output_lines


class SpecsResult(Logging):

    def __init__(self, specs: List[SpecResult]) -> None:
        self.specs = specs

    @property
    def report_lines(self) -> List[str]:
        return self.specs // _.report_lines

    @property
    def report(self) -> str:
        return self.report_lines.join_lines

    def print_report(self) -> None:
        self.log.info(self.report)


# TODO other methods: via file path, specification of single methods
def parse_spec(path: str) -> Either[str, type]:
    return Either.import_path(path)


def collect_specs(specs: List[str]) -> Either[str, List[type]]:
    return specs.traverse(parse_spec, Either)


def spec_line(spec: Any, attr: str, line: str) -> Maybe[SpecLine]:
    err = 'spec class `{}` does not define a spec `{}`'
    return (
        Maybe.getattr(spec, attr)
        .to_either(err.format(spec, attr))
        .map(L(SpecLine)(line, _))
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


def construct_runner(spec: type) -> Either[str, SpecRunner]:
    return (
        Maybe(spec.__doc__)
        .to_either('spec class `{}` has no docstring'.format(spec.__name__)) /
        List.lines //
        __.traverse(parse_line(spec), Either) /
        L(SpecRunner)(spec, _)
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
