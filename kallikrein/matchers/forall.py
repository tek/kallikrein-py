from typing import Generic, TypeVar
from typing import Collection  # type: ignore

from kallikrein.match_result import (MatchResult, SimpleMatchResult,
                                     ForAllMatchResult)

from amino import List
from kallikrein.matcher import Matcher


A = TypeVar('A')


class ForAll(Generic[A], Matcher[Collection[A]]):
    success = 'all elements of {} are == {}'
    failure = 'some elements of {} are /= {}'

    def match(self, exp: Collection[A], target: A
              ) -> MatchResult[Collection[A]]:
        result = self.target in exp
        templ = ForAll.success if result else ForAll.failure
        message = templ.format(exp, self.target)
        return SimpleMatchResult(result, message)

    def match_nested(self, exp: Collection[A], target: Matcher
                     ) -> MatchResult[Collection[A]]:
        nested = List.wrap([target.evaluate(e) for e in exp])
        return ForAllMatchResult(str(self), exp, nested)


forall = ForAll()

__all__ = ('forall',)
