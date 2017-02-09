from amino import Maybe, Either, L, _, Right, Empty, List, Boolean, Path
from amino.list import Lists
from amino.logging import Logging

from kallikrein.expectation import ExpectationResult


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


class SpecLocation:
    no_docstring_msg = 'spec class `{}` has no docstring'

    @staticmethod
    def create(mod: str, cls: str, meth: Maybe[str], selector: Selector,
               allow_empty: bool=False) -> Either[str, 'SpecLocation']:
        return (
            Either.import_name(mod, cls) /
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

    @property
    def fallback_doc(self) -> Maybe[str]:
        return self.meth // self.selector.specific.m

    @property
    def doc(self) -> Either[str, str]:
        return (
            Maybe(self.cls.__doc__)
            .o(self.fallback_doc)
            .to_either(SpecLocation.no_docstring_msg.format(self.cls.__name__))
        )


class SpecResult(Logging):

    def __init__(self, results: List[ExpectationResult]) -> None:
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

__all__ = ('SpecLocation', 'SpecResult', 'SpecsResult')
