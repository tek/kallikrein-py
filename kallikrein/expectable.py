import abc
from typing import Generic, TypeVar

from kallikrein.match_result import MatchResult
from kallikrein.matcher import Matcher

A = TypeVar('A')


class ExpectationFailed(Exception):
    pass


class ExpectableBase(Generic[A], abc.ABC):

    def __init__(self, value: A) -> None:
        self.value = value

    @abc.abstractmethod
    def match(self, matcher: Matcher[A]) -> MatchResult[A]:
        ...

    def __call__(self, matcher: Matcher[A]) -> MatchResult[A]:
        return self.match(matcher)

    must = __call__

    def safe_match(self, matcher: Matcher[A]) -> MatchResult[A]:
        return self.default_expectation(matcher)

    def unsafe_match(self, matcher: Matcher[A]) -> MatchResult[A]:
        match = self.safe_match(matcher)
        if not match.success:
            raise ExpectationFailed(match.report)
        return match

    def default_expectation(self, matcher: Matcher[A]) -> MatchResult[A]:
        return matcher(self.value)


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
