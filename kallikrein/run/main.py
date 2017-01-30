from typing import Any

from amino import (List, Either, Task, Right, curried, L, _, Maybe, __, Left,
                   Path, Just, Empty)
from amino.regex import Regex, Match
from amino.logging import Logging, amino_root_logger
from amino.task import TaskException
from amino.util.numeric import parse_int
from amino.list import Lists

from kallikrein.run.line import Line, SpecLine, PlainLine, ResultLine
from kallikrein.match_result import MatchResult


class SpecLocation:

    @staticmethod
    def create(mod: str, cls: str, meth: Maybe[str]
               ) -> Either[str, 'SpecLocation']:
        return Either.import_name(mod, cls) / L(SpecLocation)(mod, _, meth)

    @staticmethod
    def from_path(path: str) -> Either[str, 'SpecLocation']:
        parts = Lists.split(path, '.')
        return (
            Right(parts.drop_right(1).join_dot)
            .product2(Either.import_path(path), Right(Empty()))
            .o(
                Right(parts.drop_right(2).join_dot)
                .product2(Either.import_path(parts.drop_right(1).join_dot),
                          Right(parts.last))
            )
            .map3(SpecLocation)
        )

    def __init__(self, mod: str, cls: type, meth: Maybe[str]) -> None:
        self.mod = mod
        self.cls = cls
        self.meth = meth

    def __str__(self) -> str:
        return '{}({}, {}, {})'.format(self.__class__.__name__, self.mod,
                                       self.cls, self.meth)

    @property
    def doc(self) -> str:
        return (
            Maybe(self.cls.__doc__)
            .to_either('spec class `{}` has no docstring'
                       .format(self.cls.__name__))
        )


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


file_loc_regex = Regex(
    r'(?P<path>.*?)(\.(?P<cls>\w+(\.(?P<meth>\w+))?)|:(?P<lnum>\d+))?$')
cls_def_regex = Regex(r'\s*(?P<kw>class|def) (?P<name>\w+)')
cls_regex = Regex(r'\s*class (?P<name>\w+)')


def lookup_file_loc(loc: str) -> Either[str, SpecLocation]:
    init = '__init__.py'
    def module(path: Path) -> List[str]:
        return (
            module(path.parent).cat(path.name)
            if List.wrap(path.iterdir()).exists(_.name == init) else
            List()
        )
    def by_line(path: Path, mod: str, lnum: int) -> Either[str, SpecLocation]:
        content = List.lines(path.read_text())[:lnum + 1].reversed
        def found_def(name: str) -> Either[str, SpecLocation]:
            cls = content.find_map(cls_regex.match) // __.group('name')
            return cls // L(SpecLocation.create)(mod, _, Just(name))
        def found_cls_def(match: Match) -> Either[str, SpecLocation]:
            name = match.group('name')
            return (
                name // found_def
                if match.group('kw').contains('def') else
                name / L(SpecLocation.create)(mod, _, Empty())
            )
        loc = content.find_map(cls_def_regex.match)
        return loc // found_cls_def
    def by_path(match: Match, path: str) -> Either[str, SpecLocation]:
        p = Path(path)
        mod = module(p.parent).cat(p.stem).mk_string('.')
        return (
            (match.group('lnum') // parse_int // L(by_line)(p, mod, _))
            .o(match.group('cls') //
               L(SpecLocation.create)(mod, _, match.group('meth')))
            if p.is_file() else
            Left('invalid path: {}'.format(path))
        )
    def handle(match: Match) -> Either[str, SpecLocation]:
        return match.group('path') // L(by_path)(match, _)
    return file_loc_regex.match(loc) // handle


def parse_locator(loc: str) -> Either[str, SpecLocation]:

    return lookup_file_loc(loc).o(SpecLocation.from_path(loc))


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
