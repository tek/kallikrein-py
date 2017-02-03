import abc
from typing import Any, Callable

from amino import List

from kallikrein.util.string import indent, red_cross, green_check
from kallikrein.expectation import ExpectationResult, Expectation


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

    @abc.abstractmethod
    def exclude_by_name(self, name: str) -> bool:
        ...


class SimpleLine(Line):

    def exclude_by_name(self, name: str) -> bool:
        return False


class PlainLine(SimpleLine):

    @property
    def output_lines(self) -> List[str]:
        return List(self.text)


class ResultLine(SimpleLine):

    def __init__(self, text: str, spec: Any, result: ExpectationResult
                 ) -> None:
        super().__init__(text)
        self.spec = spec
        self.result = result

    @property
    def sign(self) -> str:
        return green_check if self.result.success else red_cross

    @property
    def output_lines(self) -> List[str]:
        rest = self.result.report_lines if self.result.failure else List()
        return indent(indent(rest).cons('{} {}'.format(self.sign, self.text)))

    def __str__(self) -> str:
        return '{}({})'.format(self.__class__.__name__, self.output_lines)


class SpecLine(Line):

    def __init__(self, name: str, text: str,
                 spec: Callable[[Any], Expectation]) -> None:
        super().__init__(text)
        self.name = name
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

    def exclude_by_name(self, name: str) -> bool:
        return self.name == name

__all__ = ('Line', 'PlainLine', 'SpecLine', 'ResultLine')
