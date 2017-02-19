from typing import Sized

from kallikrein.match_result import MatchResult

from amino import Boolean, _, L
from kallikrein.matcher import BoundMatcher, matcher, Predicate, Nesting


class Length:
    pass


class PredLength(Predicate):
    pass


class NestLength(Nesting):
    pass


is_sized = L(issubclass)(_, Sized)


class PredLengthSized(PredLength, pred=is_sized):

    def check(self, exp: Sized, target: int) -> Boolean:
        return Boolean(len(exp) == target)


class NestLengthSized(NestLength, pred=is_sized):

    def match(self, exp: Sized, target: BoundMatcher) -> MatchResult:
        return target.evaluate(len(exp))

    def wrap(self, name: str, exp: Sized, nested: MatchResult) -> MatchResult:
        return nested


success = '`{}` has length of `{}`'
failure = '`{}` doesn not have length of `{}`'
have_length = matcher(Length, success, failure, PredLength, NestLength)

__all__ = ('have_length',)
