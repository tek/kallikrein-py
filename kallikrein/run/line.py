import abc
from typing import Any, Callable
from datetime import timedelta

from amino import List, Boolean
from amino.task import TaskException
from amino.list import Lists

from amino.logging import Logging

from kallikrein.util.string import indent, red_cross, green_check, yellow_clock
from kallikrein.expectation import (ExpectationResult, Expectation,
                                    PendingExpectationResult)


class Line(Logging, abc.ABC):

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

    def print_report(self) -> None:
        self.output_lines % self.log.info


class SimpleLine(Line):

    def exclude_by_name(self, name: str) -> bool:
        return False


class PlainLine(SimpleLine):

    @property
    def output_lines(self) -> List[str]:
        return List(self.text)


class ResultLine(SimpleLine):

    def __init__(self, text: str, spec: Any, result: ExpectationResult,
                 duration: timedelta) -> None:
        super().__init__(text)
        self.spec = spec
        self.result = result
        self.duration = duration

    @property
    def success(self) -> Boolean:
        return self.result.success

    @property
    def sign(self) -> str:
        return (
            green_check
            if self.success else
            yellow_clock
            if isinstance(self.result, PendingExpectationResult) else
            red_cross
        )

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
        return self.name != name


class FatalLine(SimpleLine):
    header = 'error during spec run:'

    def __init__(self, error: Exception) -> None:
        self.error = error

    @property
    def output_lines(self) -> List[str]:
        e = self.error
        msg = e.cause if isinstance(e, TaskException) else e  # type: ignore
        return Lists.lines(str(msg)).cons(FatalLine.header)


__all__ = ('Line', 'PlainLine', 'SpecLine', 'ResultLine', 'FatalLine')
