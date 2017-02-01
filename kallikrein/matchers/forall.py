from typing import Generic, TypeVar, Container

from kallikrein.match_result import (MatchResult, SimpleMatchResult,
                                     ForAllMatchResult)

from amino import List
from kallikrein.matcher import Matcher, matcher


A = TypeVar('A')


class ForAll(Generic[A], Matcher[Container[A]]):

    def match(self, exp: Container[A], target: A) -> MatchResult[Container[A]]:
        success = 'all elements of {} are == {}'.format(exp, self.target)
        failure = 'some elements of {} are /= {}'.format(exp, self.target)
        return SimpleMatchResult(self.target in exp, success, failure)

    def match_nested(self, exp: Container[A], target: Matcher
                     ) -> MatchResult[Container[A]]:
        nested = List.wrap([target(e) for e in exp])
        return ForAllMatchResult(str(self), exp, nested)


forall = matcher(ForAll)

__all__ = ('forall',)
