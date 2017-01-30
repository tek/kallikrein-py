from amino import Maybe, Either, L, _, Right, Empty, List
from amino.list import Lists
from amino.logging import Logging

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

__all__ = ('SpecLocation', 'SpecResult', 'SpecsResult')