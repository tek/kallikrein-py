from typing import Generic, TypeVar
from typing import Collection  # type: ignore

from kallikrein.match_result import (MatchResult, SimpleMatchResult,
                                     ExistsMatchResult)

from amino import Boolean, List
from kallikrein.matcher import Matcher, matcher

A = TypeVar('A')


class Contain(Generic[A], Matcher[Collection[A]]):
    success = '`{}` contains `{}`'
    failure = '`{}` does not contain `{}`'

    def match(self, exp: Collection[A], target: A
              ) -> MatchResult[Collection[A]]:
        result = Boolean(self.target in exp)
        templ = Contain.success if result else Contain.failure
        message = templ.format(exp, self.target)
        return SimpleMatchResult(result, message)

    def match_nested(self, exp: Collection[A], target: Matcher
                     ) -> MatchResult[Collection[A]]:
        nested = List.wrap([target.evaluate(e) for e in exp])
        return ExistsMatchResult(str(self), exp, nested)


contain = matcher(Contain)

__all__ = ('contain',)
