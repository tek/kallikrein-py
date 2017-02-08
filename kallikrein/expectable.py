import abc
from typing import Generic, TypeVar

from amino import _, List

from kallikrein.match_result import MatchResult
from kallikrein.matcher import Matcher
from kallikrein.expectation import (UnsafeExpectation, SingleExpectation,
                                    ExpectationFailed)
from kallikrein.matchers import equal

A = TypeVar('A')


class ExpectableBase(Generic[A], abc.ABC):

    def __init__(self, value: A) -> None:
        self.value = value

    @abc.abstractmethod
    def match(self, matcher: Matcher[A]) -> MatchResult[A]:
        ...

    def __call__(self, matcher: Matcher[A]) -> MatchResult[A]:
        return self.match(matcher)

    must = __call__

    def __eq__(self, value: A) -> MatchResult[A]:  # type: ignore
        return self.must(equal(value))

    def safe_match(self, matcher: Matcher[A]) -> SingleExpectation:
        return self.default_expectation(matcher)

    def unsafe_match(self, matcher: Matcher[A]) -> UnsafeExpectation:
        expectation = self.safe_match(matcher)
        expectation.fatal_eval()
        return UnsafeExpectation(matcher, self.value)

    def default_expectation(self, matcher: Matcher[A]) -> MatchResult[A]:
        return SingleExpectation(matcher, self.value)


class Expectable(ExpectableBase):

    def match(self, matcher: Matcher[A]) -> MatchResult[A]:
        return self.safe_match(matcher)


class UnsafeExpectable(ExpectableBase):

    def match(self, matcher: Matcher[A]) -> MatchResult[A]:
        return self.unsafe_match(matcher)


def k(value: A) -> ExpectableBase[A]:
    return Expectable(value)


def unsafe_k(value: A) -> ExpectableBase[A]:
    return UnsafeExpectable(value)

__all__ = ('Expectable', 'k', 'ExpectationFailed', 'UnsafeExpectable')
