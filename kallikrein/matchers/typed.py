from typing import Generic, TypeVar, Union

from kallikrein.matcher import Matcher, matcher

from amino import List, L, _
from kallikrein.match_result import (MatchResult, SimpleMatchResult,
                                     ForAllMatchResult)
from kallikrein.matchers.any import AnyMatcher

A = TypeVar('A')


class TypedMatcher(Generic[A], Matcher[A]):
    success = '`{}` is a `{}`'
    failure = '`{}` is not a `{}`'

    def __init__(self, tpe: type, target: Union[A, Matcher]) -> None:
        super().__init__(target)
        self.tpe = tpe

    def match(self, exp: A, target: A) -> MatchResult[A]:
        result = isinstance(exp, self.tpe)
        templ = TypedMatcher.success if result else TypedMatcher.failure
        message = templ.format(exp, self.tpe)
        return SimpleMatchResult(result, message)

    def match_nested(self, exp: A, target: Matcher) -> MatchResult[A]:
        return ForAllMatchResult(
            'typed', exp, List(self.match(exp, exp), target.evaluate(exp)))


def typed(tpe: type, nested: Matcher) -> Matcher:
    return matcher(L(TypedMatcher)(tpe, _))(nested)


def have_type(tpe: type) -> Matcher:
    return typed(tpe, AnyMatcher())

__all__ = ('TypedMatcher', 'typed', 'have_type')
