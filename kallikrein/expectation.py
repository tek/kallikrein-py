import abc
import operator
import traceback
import functools
from typing import Generic, TypeVar, Callable, Any

from amino import Boolean, Task, L, _, List, __
from amino.boolean import false, true
from amino.tc.monoid import Monoid

from kallikrein.matcher import BoundMatcher
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


class PendingExpectationResult(ExpectationResult):

    def __init__(self, exp: 'Expectation') -> None:
        self.exp = exp

    @property
    def success(self) -> Boolean:
        return false

    @property
    def report_lines(self) -> List[str]:
        return List('pending')


class InvalidExpectation(Exception):

    def __init__(self, exp: 'Expectation') -> None:
        self.exp = exp
        super().__init__('cannot concat {} to Expectation'.format(exp))


class Expectation(Generic[A], abc.ABC):

    @abc.abstractproperty
    def evaluate(self) -> Task[ExpectationResult]:
        ...

    @property
    def unsafe_eval(self) -> Boolean:
        return self.evaluate.attempt.exists(_.success)

    def fatal_eval(self) -> None:
        result = self.evaluate.attempt
        if not result.exists(_.success):
            raise ExpectationFailed(result.map(_.report_lines) | List())


class AlgExpectation(Expectation):

    @abc.abstractmethod
    def __and__(self, other: 'AlgExpectation') -> 'AlgExpectation':
        ...

    @abc.abstractmethod
    def __or__(self, other: 'AlgExpectation') -> 'AlgExpectation':
        ...


class SingleExpectation(AlgExpectation):

    def __init__(self, match: BoundMatcher, value: A) -> None:
        self.match = match
        self.value = value

    @property
    def evaluate(self) -> Task[ExpectationResult]:
        return (Task.delay(self.match.evaluate, self.value) /
                L(SingleExpectationResult)(self, _))

    def __str__(self) -> str:
        return '{}({}, {})'.format(self.__class__.__name__, self.match,
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


class AlgExpectationMonoid(Monoid, tpe=AlgExpectation):

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


class PendingExpectation(Expectation):

    def __init__(self, original: Callable[[Any], Expectation]) -> None:
        self.original = original

    @property
    def evaluate(self) -> Task[ExpectationResult]:
        return Task.now(PendingExpectationResult(self))


def pending(f: Callable[[Any], Expectation]) -> Callable[[Any], Expectation]:
    @functools.wraps(f)
    def wrapper(self: Any) -> Expectation:
        return PendingExpectation(f)
    return wrapper

__all__ = ('Expectation', 'SingleExpectation', 'UnsafeExpectation',
           'unsafe_expectation_result', 'FatalSpec', 'FailedUnsafeSpec',
           'pending')
