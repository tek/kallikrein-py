from typing import Any

from kallikrein.matcher import Matcher
from kallikrein.match_result import MatchResult, SimpleMatchResult


class AnyMatcher(Matcher[Any]):

    def match(self, exp: Any, target: Any) -> MatchResult[Any]:
        return SimpleMatchResult(True, 'true')

    def match_nested(self, exp: Any, target: Matcher) -> MatchResult[Any]:
        return SimpleMatchResult(True, 'true')


be_any = AnyMatcher()(True)

__all__ = ('AnyMatcher', 'be_any')
