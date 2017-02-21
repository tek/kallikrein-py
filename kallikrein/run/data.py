import inspect
from typing import Any
from types import FunctionType
from datetime import timedelta

from amino import Maybe, Either, L, _, Right, Empty, List, Boolean, Path
from amino.list import Lists
from amino.logging import Logging
from amino.util.string import snake_case
from amino.instances.std.datetime import TimedeltaInstances  # NOQA
from amino.lazy import lazy

from kallikrein.run.line import Line, ResultLine
from kallikrein.util.string import green_check, red_cross


class Selector:

    @property
    def specific(self) -> Boolean:
        return Boolean(isinstance(self, (MethodSelector, FileMethodSelector)))


class ModuleSelector(Selector):

    def __init__(self, mod: str) -> None:
        self.mod = mod


class ClassSelector(Selector):

    def __init__(self, mod: str, cls: str) -> None:
        self.mod = mod
        self.cls = cls


class MethodSelector(Selector):

    def __init__(self, mod: str, cls: str, method: str) -> None:
        self.mod = mod
        self.cls = cls
        self.method = method


class DirSelector(Selector):

    def __init__(self, path: Path) -> None:
        self.path = path


class FileSelector(Selector):

    def __init__(self, path: Path) -> None:
        self.path = path


class FileClassSelector(Selector):

    def __init__(self, path: Path, cls: str) -> None:
        self.path = path
        self.cls = cls


class FileMethodSelector(Selector):

    def __init__(self, path: Path, cls: str, method: str) -> None:
        self.path = path
        self.cls = cls
        self.method = method


class LineSelector(Selector):

    def __init__(self, path: str, lnum: int) -> None:
        self.path = path
        self.lnum = lnum


def convert_underscores(data: str) -> str:
    return data.replace('_', ' ')


invalid_spec_names = List('setup', 'teardown')


class SpecLocation:
    no_docstring_msg = 'spec class `{}` has no docstring'

    @staticmethod
    def create(mod: str, cls: str, meth: Maybe[str], selector: Selector,
               allow_empty: bool=False) -> Either[str, 'SpecLocation']:
        return (
            Either.import_name(mod, cls)
            .filter(inspect.isclass) /
            L(SpecLocation)(mod, _, meth, selector, allow_empty)
        )

    @staticmethod
    def from_path(path: str) -> Either[str, 'SpecLocation']:
        parts = Lists.split(path, '.')
        def create(mod: str, cls: type, meth: Maybe[str]) -> SpecLocation:
            selector = (
                meth /
                L(MethodSelector)(mod, cls.__name__, _) |
                ClassSelector(mod, cls.__name__)
            )
            return SpecLocation(mod, cls, meth, selector)
        return (
            Right(parts.drop_right(1).join_dot)
            .product2(Either.import_path(path), Right(Empty()))
            .o(
                Right(parts.drop_right(2).join_dot)
                .product2(Either.import_path(parts.drop_right(1).join_dot),
                          Right(parts.last))
            )
            .map3(create)
        )

    def __init__(self, mod: str, cls: type, meth: Maybe[str],
                 selector: Selector, allow_empty: bool=False) -> None:
        self.mod = mod
        self.cls = cls
        self.meth = meth
        self.selector = selector
        self.allow_empty = Boolean(allow_empty)

    def __str__(self) -> str:
        return '{}({}, {}, {}, {})'.format(self.__class__.__name__, self.mod,
                                           self.cls, self.meth,
                                           self.allow_empty)

    def __repr__(self) -> str:
        return str(self)

    @property
    def use_all_specs(self) -> Boolean:
        return Boolean(hasattr(self.cls, '__all_specs__'))

    @property
    def need_no_doc(self) -> Boolean:
        return self.selector.specific | self.use_all_specs

    @property
    def cls_methods(self) -> List[str]:
        def filt(member: Any) -> bool:
            return (
                isinstance(member, FunctionType) and
                not member.__name__.startswith('_') and
                member.__name__ not in invalid_spec_names
            )
        valid = inspect.getmembers(self.cls, predicate=filt)
        return Lists.wrap(valid) / Lists.wrap // _.head

    @property
    def fallback_doc(self) -> Maybe[str]:
        meth = lambda name: '{} ${}'.format(convert_underscores(name), name)
        def synthetic() -> List[str]:
            meths = (self.meth / meth / List) | (self.cls_methods / meth)
            cls = convert_underscores(snake_case(self.cls.__name__))
            return meths.cons(cls).join_lines
        return self.need_no_doc.m(synthetic)

    @property
    def doc(self) -> Either[str, str]:
        return (
            Maybe(self.cls.__doc__)
            .o(lambda: self.fallback_doc)
            .to_either(SpecLocation.no_docstring_msg.format(self.cls.__name__))
        )


class SpecResult(Logging):

    def __init__(self, results: List[Line]) -> None:
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

    @lazy
    def results(self) -> List[ResultLine]:
        return (self.specs // _.results).filter_type(ResultLine)

    @lazy
    def duration(self) -> timedelta:
        return (self.results / _.duration).fold(timedelta)

    @property
    def duration_fmt(self) -> str:
        d = self.duration
        total = d.total_seconds()
        ms = int(d.microseconds / 1000)
        s = d.seconds % 60
        m = int((total / 60) % 60)
        h = int(total / 3600)
        return (
            '{}ms'.format(ms)
            if d < timedelta(seconds=1) else
            '{}.{}s'.format(s, ms)
            if d < timedelta(seconds=10) else
            '{}s'.format(s)
            if d < timedelta(minutes=1) else
            '{}min {}s'.format(m, s)
            if d < timedelta(hours=1) else
            '{}h {}min'.format(h, m)
        )

    @property
    def success_count(self) -> int:
        return self.results.filter(_.success).length

    @property
    def failure_count(self) -> int:
        return self.results.length - self.success_count

    @property
    def success(self) -> bool:
        return self.failure_count == 0

    @property
    def stats(self) -> str:
        return '{} specs in {}:  {} {}  {} {}'.format(
            self.results.length,
            self.duration_fmt,
            green_check,
            self.success_count,
            red_cross,
            self.failure_count
        )

    @property
    def stats_lines(self) -> List[str]:
        return List(self.stats)

    def print_stats(self) -> None:
        self.stats_lines % self.log.info

    @property
    def report_with_stats_lines(self) -> List[str]:
        return self.report_lines.cat(self.stats_lines)

    @property
    def report_with_stats(self) -> str:
        return self.report_with_stats_lines.join_lines

    def print_report(self) -> None:
        self.report_with_stats_lines % self.log.info

__all__ = ('SpecLocation', 'SpecResult', 'SpecsResult')
