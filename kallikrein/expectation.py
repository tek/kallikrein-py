import abc
import operator
import traceback
from typing import Generic, TypeVar, Callable

from amino import Boolean, Task, L, _, List, __, Map
from amino.boolean import false, true
from amino.tc.monoid import Monoid
from amino.tc.base import AutoImplicitInstances
from amino.lazy import lazy

from kallikrein.matcher import Matcher
from kallikrein.match_result import MatchResult, SuccessMatchResult
from kallikrein.util.string import indent, red

A = TypeVar('A')
B = TypeVar('B')


class ExpectationFailed(Exception):

    def __init__(self, report: List[str]) -> None:
        self.report = report


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

    def __init__(self, exp: 'Expectation', result: MatchResult) -> None:
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


class UnsafeExpectationResult(ExpectationResult):

    @property
    def success(self) -> Boolean:
        return true

    @property
    def report_lines(self) -> List[str]:
        return List('unsafe spec succeeded')


unsafe_expectation_result = UnsafeExpectationResult()


class FatalSpecResult(ExpectationResult):
    error_head = 'exception during spec:'

    def __init__(self, name: str, error: Exception) -> None:
        self.name = name
        self.error = error

    @property
    def success(self) -> Boolean:
        return false

    @property
    def report_lines(self) -> List[str]:
        stack = (List.wrap(traceback.extract_tb(self.error.__traceback__))
                 .drop_while(_.name != self.name))
        exc = traceback.format_exception_only(type(self.error), self.error)
        exc_fmt = (
            List.wrap(exc) /
            __.rstrip() /
            red
        )
        lines = List.lines(''.join(traceback.format_list(stack))) / __.rstrip()
        return indent(lines + exc_fmt).cons(FatalSpecResult.error_head)


class FailedUnsafeSpecResult(ExpectationResult):

    def __init__(self, name: str, error: ExpectationFailed) -> None:
        self.name = name
        self.error = error

    @property
    def success(self) -> Boolean:
        return false

    @property
    def report_lines(self) -> List[str]:
        return indent(self.error.report).cons('unsafe spec failed:')


class InvalidExpectation(Exception):

    def __init__(self, exp: 'Expectation') -> None:
        self.exp = exp
        super().__init__('cannot concat {} to Expectation'.format(exp))


class Expectation(Generic[A], abc.ABC):

    @abc.abstractproperty
    def evaluate(self) -> Task[ExpectationResult]:
        ...


class AlgExpectation(Expectation):

    @abc.abstractmethod
    def __and__(self, other: 'AlgExpectation') -> 'AlgExpectation':
        ...

    @abc.abstractmethod
    def __or__(self, other: 'AlgExpectation') -> 'AlgExpectation':
        ...


class SingleExpectation(AlgExpectation):

    def __init__(self, matcher: Matcher[A], value: A) -> None:
        self.matcher = matcher
        self.value = value

    @property
    def evaluate(self) -> Task[ExpectationResult]:
        return (Task.delay(self.matcher.evaluate, self.value) /
                L(SingleExpectationResult)(self, _))

    def __str__(self) -> str:
        return '{}({}, {})'.format(self.__class__.__name__, self.matcher,
                                   self.value)

    def __and__(self, other: AlgExpectation) -> AlgExpectation:
        return MultiExpectation(self, other, operator.and_)

    def __or__(self, other: AlgExpectation) -> AlgExpectation:
        return MultiExpectation(self, other, operator.or_)


class MultiExpectation(AlgExpectation):

    def __init__(self, left: SingleExpectation, right: AlgExpectation,
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

    def __and__(self, other: AlgExpectation) -> AlgExpectation:
        return MultiExpectation(self.left, self.right & other, self.op)

    def __or__(self, other: AlgExpectation) -> AlgExpectation:
        return MultiExpectation(self.left, self.right | other, self.op)


class UnsafeExpectation(SingleExpectation):

    @property
    def evaluate(self) -> Task[ExpectationResult]:
        return Task.now(SingleExpectationResult(self, SuccessMatchResult()))


class EmptyExpectation(AlgExpectation):

    @property
    def evaluate(self) -> Task[ExpectationResult]:
        return Task.now(SingleExpectationResult(self, SuccessMatchResult()))

    def __and__(self, other: AlgExpectation) -> AlgExpectation:
        return other

    def __or__(self, other: AlgExpectation) -> AlgExpectation:
        return other


class AlgExpectationInstances(AutoImplicitInstances):
    tpe = AlgExpectation

    @lazy
    def _instances(self) -> Map:
        return Map(
            {
                Monoid: AlgExpectationMonoid(),
            }
        )


class AlgExpectationMonoid(Monoid):

    @property
    def empty(self) -> AlgExpectation:
        return EmptyExpectation()

    def combine(self, left: AlgExpectation, right: AlgExpectation
                ) -> AlgExpectation:
        return left & right


class FatalSpec(Expectation):

    def __init__(self, name: str, error: Exception) -> None:
        self.name = name
        self.error = error

    @property
    def evaluate(self) -> Task[ExpectationResult]:
        return Task.now(FatalSpecResult(self.name, self.error))


class FailedUnsafeSpec(Expectation):

    def __init__(self, name: str, error: ExpectationFailed) -> None:
        self.name = name
        self.error = error

    @property
    def evaluate(self) -> Task[ExpectationResult]:
        return Task.now(FailedUnsafeSpecResult(self.name, self.error))

__all__ = ('Expectation', 'SingleExpectation', 'UnsafeExpectation',
           'unsafe_expectation_result', 'FatalSpec', 'FailedUnsafeSpec')
