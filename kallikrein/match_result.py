import abc
from typing import Generic, TypeVar, Any

from hues import huestr

from amino import Boolean, List, _

from kallikrein.util.string import indent

A = TypeVar('A')
B = TypeVar('B')


class MatchResult(Generic[A], abc.ABC):

    @abc.abstractproperty
    def success(self) -> Boolean:
        ...

    @property
    def failure(self) -> Boolean:
        return not self.success

    @abc.abstractproperty
    def success_message(self) -> List[str]:
        ...

    @abc.abstractproperty
    def failure_message(self) -> List[str]:
        ...

    @property
    def report_lines(self) -> List[str]:
        return self.success_message if self.success else self.failure_message

    @property
    def report(self) -> str:
        return self.report_lines.join_lines

    def __str__(self) -> str:
        return '{}({})'.format(self.__class__.__name__, self.report)


class SimpleMatchResult(Generic[A, B], MatchResult[A]):

    def __init__(
            self,
            result: Boolean,
            success: str,
            failure: str,
    ) -> None:
        self.result = result
        self.success_msg = success
        self.failure_msg = failure

    @property
    def success(self) -> Boolean:
        return self.result

    @property
    def success_message(self) -> List[str]:
        return List(self.success_msg)

    @property
    def failure_message(self) -> List[str]:
        return List(self.failure_msg)


class ComplexMatchResult(Generic[A, B], MatchResult[A], abc.ABC):
    success_message_template = '{} succeeded'
    failure_message_template = '{} has failures for {}: {}'

    def __init__(self, desc: str, exp: A, results: List[MatchResult]) -> None:
        self.desc = desc
        self.exp = exp
        self.results = results

    @property
    def failures(self) -> List[MatchResult]:
        return self.results.filter_not(_.success)

    @abc.abstractproperty
    def success(self) -> Boolean:
        ...

    @property
    def success_message(self) -> List[str]:
        return List(self.success_message_template.format(self.desc))

    @property
    def failure_message(self) -> List[str]:
        return self._failure_message('complex match failed for')

    def _failure_message(self, desc: str) -> List[str]:
        reports = self.failures / _.report / huestr / _.yellow.colorized
        return indent(reports).cons('{}:'.format(desc))


class ExistsMatchResult(ComplexMatchResult):

    @property
    def success(self) -> Boolean:
        return self.results.exists(_.success)

    @property
    def failure_message(self) -> List[str]:
        return self._failure_message('no elements match')


class ForAllMatchResult(ComplexMatchResult):

    @property
    def success(self) -> Boolean:
        return self.failures.empty

    @property
    def failure_message(self) -> List[str]:
        return self._failure_message('some elements do not match')


class BadNestedMatch(MatchResult[Any]):

    def __init__(self, matcher: Any) -> None:
        self.matcher = matcher

    @property
    def message(self) -> List[str]:
        return List('`{}` cannot take nested matchers')

    success_message = message
    failure_message = message


__all__ = ('MatchResult', 'SimpleMatchResult')
