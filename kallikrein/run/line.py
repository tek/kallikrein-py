import abc
from typing import Any, Callable

from hues import huestr

from amino import List

from kallikrein.match_result import MatchResult
from kallikrein.util.string import indent


class Line(abc.ABC):

    def __init__(self, text: str) -> None:
        self.text = text.strip()

    @abc.abstractproperty
    def output_lines(self) -> List[str]:
        ...

    @property
    def output(self) -> str:
        return self.output_lines.join_lines

    def __str__(self) -> str:
        return '{}({!r})'.format(self.__class__.__name__, self.text)


class PlainLine(Line):

    @property
    def output_lines(self) -> List[str]:
        return List(self.text)


class ResultLine(Line):

    def __init__(self, text: str, spec: Any, result: MatchResult) -> None:
        super().__init__(text)
        self.spec = spec
        self.result = result

    @property
    def sign(self) -> str:
        return (
            huestr('✓').green.colorized
            if self.result.success else
            huestr('✗').red.colorized
        )

    @property
    def output_lines(self) -> List[str]:
        rest = self.result.report_lines if self.result.failure else List()
        return indent(indent(rest).cons('{} {}'.format(self.sign, self.text)))

    def __str__(self) -> str:
        return '{}({})'.format(self.__class__.__name__, self.output)


class SpecLine(Line):

    def __init__(self, text: str, spec: Callable[[Any], MatchResult]) -> None:
        super().__init__(text)
        self.spec = spec

    @property
    def output_lines(self) -> List[str]:
        return List('{} {}'.format(self.text, self.spec))

    @property
    def spec_name(self) -> str:
        pre = (
            '{}.'.format(self.spec.__self__.__class__.__name__)  # type: ignore
            if hasattr(self.spec, '__self__') else
            ''
        )
        return '{}{}'.format(pre, self.spec.__name__)

    def __str__(self) -> str:
        return '{}({}, {})'.format(self.__class__.__name__, self.text,
                                   self.spec_name)

__all__ = ('Line', 'PlainLine', 'SpecLine', 'ResultLine')
