from typing import Sized

from kallikrein.match_result import (MatchResult, SimpleMatchResult,
                                     BadNestedMatch)

from amino import Boolean
from amino.boolean import false
from kallikrein.matcher import Matcher, matcher


class Length(Matcher[Sized]):

    def _check(self, exp: Sized, target: int) -> MatchResult[Sized]:
        actual = len(exp)
        result = Boolean(actual == target)
        no = '' if result else '{}, not '.format(actual)
        message = 'length of {} is {}{}'.format(exp, no, target)
        return SimpleMatchResult(result, message)

    def match(self, exp: Sized, target: int) -> MatchResult[Sized]:
        return (
            self._check(exp, target)
            if hasattr(exp, '__len__') else
            SimpleMatchResult(false, '`{}` has no length'.format(exp))
        )

    def match_nested(self, exp: Sized, target: Matcher) -> MatchResult[Sized]:
        return BadNestedMatch(self)

length = matcher(Length)
have_length = length

__all__ = ('Length', 'length', 'have_length')
