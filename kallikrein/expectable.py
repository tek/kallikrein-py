import abc
from typing import Generic, TypeVar, Union, Callable, Any

from kallikrein.match_result import MatchResult
from kallikrein.matcher import Matcher, BoundMatcher
from kallikrein.expectation import (UnsafeExpectation, SingleExpectation,
                                    ExpectationFailed, SingleStrictExpectation,
                                    SingleCallableExpectation)
from kallikrein.matchers import equal
from kallikrein.matchers.any import be_any

A = TypeVar('A')


class ExpectableBase(Generic[A]):

    def __init__(self, value: A) -> None:
        self.value = value

    @abc.abstractmethod
    def match(self, match: BoundMatcher) -> MatchResult[A]:
        ...

    def __call__(self, mm: Union[BoundMatcher, Matcher[A]]) -> MatchResult[A]:
        match = mm if isinstance(mm, BoundMatcher) else mm(be_any)
        return self.match(match)

    must = __call__
    should = __call__

    def safe_match(self, matcher: BoundMatcher) -> SingleExpectation:
        return self.default_expectation(matcher)

    def unsafe_match(self, matcher: BoundMatcher) -> UnsafeExpectation:
        expectation = self.safe_match(matcher)
        expectation.fatal_eval()
        return UnsafeExpectation(matcher, self.value)

    def default_expectation(self, matcher: BoundMatcher) -> MatchResult[A]:
        return SingleStrictExpectation(matcher, self.value)

    def __eq__(self, value: A) -> MatchResult[A]:  # type: ignore
        return self.must(equal(value))

    @property
    def true(self) -> MatchResult[A]:
        return self.must(equal(True))

    @property
    def false(self) -> MatchResult[A]:
        return self.must(equal(False))


class Expectable(ExpectableBase):

    def match(self, matcher: BoundMatcher) -> MatchResult[A]:
        return self.safe_match(matcher)


class UnsafeExpectable(ExpectableBase):

    def match(self, matcher: BoundMatcher) -> MatchResult[A]:
        return self.unsafe_match(matcher)


class CallableExpectable(ExpectableBase):

    def __init__(self, value: Callable[..., A], a: Any, kw: Any) -> None:
        self.value = value
        self.a = a
        self.kw = kw

    def match(self, matcher: BoundMatcher) -> MatchResult[A]:
        return SingleCallableExpectation(matcher, self.value, self.a, self.kw)


def k(value: A) -> ExpectableBase[A]:
    return Expectable(value)


def unsafe_k(value: A) -> ExpectableBase[A]:
    return UnsafeExpectable(value)


def kf(value: Callable[..., A], *a: Any, **kw: Any) -> ExpectableBase[A]:
    return CallableExpectable(value, a, kw)

__all__ = ('Expectable', 'k', 'ExpectationFailed', 'UnsafeExpectable')
