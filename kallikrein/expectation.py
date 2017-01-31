import abc
import operator
from typing import Generic, TypeVar, Callable

from amino import Boolean, Task, L, _, List

from kallikrein.matcher import Matcher
from kallikrein.match_result import MatchResult, SuccessMatchResult

A = TypeVar('A')
B = TypeVar('B')


class ExpectationResult(abc.ABC):

    @abc.abstractproperty
    def success(self) -> Boolean:
        ...

    @property
    def failure(self) -> Boolean:
        return not self.success

    @abc.abstractproperty
    def report_lines(self) -> List[str]:
        ...

    @property
    def report(self) -> str:
        return self.report_lines.join_lines


class SingleExpectationResult(ExpectationResult):

    def __init__(self, exp: 'SingleExpectation', result: MatchResult) -> None:
        self.exp = exp
        self.result = result

    @property
    def success(self) -> Boolean:
        return self.result.success

    def __str__(self) -> str:
        return '{}({}, {})'.format(self.__class__.__name__, self.exp,
                                   self.result)

    @property
    def report_lines(self) -> List[str]:
        return self.result.report_lines


class MultiExpectationResult(ExpectationResult):

    def __init__(self, exp: 'MultiExpectation', left: ExpectationResult,
                 right: ExpectationResult,
                 op: Callable[[bool, bool], bool]) -> None:
        self.exp = exp
        self.left = left
        self.right = right
        self.op = op

    @property
    def success(self) -> Boolean:
        return self.op(self.left.success, self.right.success)

    def __str__(self) -> str:
        return '{}({}, {}, {}, {})'.format(self.__class__.__name__, self.exp,
                                           self.left, self.right,
                                           self.op.__name__)

    @property
    def report_lines(self) -> List[str]:
        return self.left.report_lines + self.right.report_lines


class InvalidExpectation(Exception):

    def __init__(self, exp: 'Expectation') -> None:
        self.exp = exp
        super().__init__('cannot concat {} to Expectation'.format(exp))


class Expectation(Generic[A], abc.ABC):

    @abc.abstractproperty
    def evaluate(self) -> Task[ExpectationResult]:
        ...

    @abc.abstractmethod
    def __and__(self, other: 'Expectation') -> 'MultiExpectation':
        ...

    @abc.abstractmethod
    def __or__(self, other: 'Expectation') -> 'MultiExpectation':
        ...


class SingleExpectation(Expectation):

    def __init__(self, matcher: Matcher[A], value: A) -> None:
        self.matcher = matcher
        self.value = value

    @property
    def evaluate(self) -> Task[ExpectationResult]:
        return (Task.delay(self.matcher, self.value) /
                L(SingleExpectationResult)(self, _))

    def __str__(self) -> str:
        return '{}({}, {})'.format(self.__class__.__name__, self.matcher,
                                   self.value)

    def __and__(self, other: Expectation) -> 'MultiExpectation':
        return MultiExpectation(self, other, operator.and_)

    def __or__(self, other: Expectation) -> 'MultiExpectation':
        return MultiExpectation(self, other, operator.or_)


class MultiExpectation(Expectation):

    def __init__(self, left: SingleExpectation, right: Expectation,
                 op: Callable[[bool, bool], bool]) -> None:
        self.left = left
        self.right = right
        self.op = op

    @property
    def evaluate(self) -> Task[ExpectationResult]:
        return (
            (self.left.evaluate & self.right.evaluate)
            .map2(L(MultiExpectationResult)(self, _, _, self.op))
        )

    def __str__(self) -> str:
        return '{}({}, {})'.format(self.__class__.__name__, self.left,
                                   self.right)

    def __and__(self, other: Expectation) -> 'MultiExpectation':
        return MultiExpectation(self.left, self.right & other, self.op)

    def __or__(self, other: Expectation) -> 'MultiExpectation':
        return MultiExpectation(self.left, self.right | other, self.op)


class UnsafeExpectation(SingleExpectation):

    @property
    def evaluate(self) -> Task[ExpectationResult]:
        return Task.now(SingleExpectationResult(self, SuccessMatchResult()))


__all__ = ('Expectation', 'SingleExpectation', 'UnsafeExpectation')
