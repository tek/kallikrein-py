import abc
from typing import Any, Tuple, Union, TypeVar

from kallikrein.matcher import Matcher
from kallikrein.match_result import MatchResult, NestedMatchResult
from kallikrein.matchers.any import be_any
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

    def _match_type(self, exp: Either) -> Tuple[bool, str]:
        actual = either_name(self.right_expected)
        success = (isinstance(exp, Either) and
                   exp.is_right == self.right_expected)
        no = '' if success else 'not '
        msg = EitherMatcher.type_message.format(exp, no, actual)
        return success, msg

    def match(self, exp: Either, target: Any) -> MatchResult:
        return self.match_nested(exp, equal(target))

    def match_nested(self, exp: Either, target: Matcher) -> MatchResult:
        type_result, msg = self._match_type(exp)
        nested = target.evaluate(exp.value)
        return NestedMatchResult(exp, type_result, msg, List(nested))

    def __call__(self, target: Union[A, Matcher[A]]) -> 'EitherMatcher':
        return type(self)(target)  # type: ignore


class RightMatcher(EitherMatcher):

    @property
    def right_expected(self) -> bool:
        return True


class LeftMatcher(EitherMatcher):

    @property
    def right_expected(self) -> bool:
        return False


be_right = RightMatcher(be_any)
be_left = LeftMatcher(be_any)

__all__ = ('EitherMatcher',)
