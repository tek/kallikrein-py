from typing import Union, TypeVar

from kallikrein.matchers.typed import have_type, ChainTyped
from kallikrein.matchers import contain
from kallikrein.matcher import StrictMatcher, BoundMatcher
from kallikrein.matchers.contain import PredContain

from amino import Right, Left, Either, Boolean

A = TypeVar('A')
B = TypeVar('B')


class ChainTypedEither(ChainTyped, tpe=Either):

    def chain(self, matcher: StrictMatcher, other: Union[A, BoundMatcher]) -> BoundMatcher:
        return matcher & contain(other)


class PredContainEither(PredContain, tpe=Either):

    def check(self, exp: Either[A, B], target: Union[A, B]) -> Boolean:
        return Boolean(exp.value == target)


be_right = have_type(Right)
be_left = have_type(Left)

__all__ = ('be_right', 'be_left')
