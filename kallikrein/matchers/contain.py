from typing import Generic, TypeVar, Container

from kallikrein.match_result import (MatchResult, SimpleMatchResult,
                                     ExistsMatchResult)

from amino import Boolean, List
from kallikrein.matcher import Matcher, matcher

A = TypeVar('A')


class Contain(Generic[A], Matcher[Container[A]]):
    success = '`{}` contains `{}`'
    failure = '`{}` does not contain `{}`'

    def match(self, exp: Container[A], target: A) -> MatchResult[Container[A]]:
        success = Contain.success.format(exp, self.target)
        failure = Contain.failure.format(exp, self.target)
        return SimpleMatchResult(Boolean(self.target in exp), success, failure)

    def match_nested(self, exp: Container[A], target: Matcher
                     ) -> MatchResult[Container[A]]:
        nested = List.wrap([target(e) for e in exp])
        return ExistsMatchResult(str(self), exp, nested)


contain = matcher(Contain)

__all__ = ('contain',)
