from kallikrein.matcher import Matcher
from kallikrein.match_result import (SimpleMatchResult, MatchResult,
                                     BadNestedMatch)

from amino import Either, Boolean


class EitherMatcher(Matcher[Either]):

    def match(self, exp: Either, target: Boolean) -> MatchResult:
        return SimpleMatchResult(exp.is_right == target,
                                 '`{}` is right'.format(exp),
                                 '`{}` is left'.format(exp))

    def match_nested(self, exp: Either, target: Matcher) -> MatchResult:
        return BadNestedMatch(self)


be_right = EitherMatcher(Boolean(True))
be_left = EitherMatcher(Boolean(False))

__all__ = ('EitherMatcher',)
