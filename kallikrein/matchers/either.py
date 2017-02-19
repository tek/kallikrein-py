import abc
from typing import Any, TypeVar

from kallikrein.matcher import BoundMatcher, Matcher
from kallikrein.match_result import MatchResult, NestedMatchResult
from kallikrein.matchers import equal

from amino import Either, List

A = TypeVar('A')


def either_name(right: bool) -> str:
    return 'right' if right else 'left'


class EitherMatcher(Matcher[Either]):
    type_message = '`{}` is {}{}'

    @abc.abstractproperty
    def right_expected(self) -> bool:
        ...

    def format(self, success: bool, exp: Either, target: Any) -> str:
        actual = either_name(self.right_expected)
        no = '' if success else 'not '
        return EitherMatcher.type_message.format(exp, no, actual)

    def _match_type(self, exp: Either) -> bool:
        return isinstance(exp, Either) and exp.is_right == self.right_expected

    def match(self, exp: Either, target: Any) -> MatchResult:
        return self.match_nested(exp, equal(target))

    def match_nested(self, exp: Either, target: BoundMatcher) -> MatchResult:
        type_result = self._match_type(exp)
        msg = self.format(type_result, exp, target)
        nested = target.evaluate(exp.value)
        return NestedMatchResult(exp, type_result, msg, List(nested))


class RightMatcher(EitherMatcher):

    @property
    def right_expected(self) -> bool:
        return True


class LeftMatcher(EitherMatcher):

    @property
    def right_expected(self) -> bool:
        return False


be_right = RightMatcher()
be_left = LeftMatcher()

__all__ = ('EitherMatcher',)
