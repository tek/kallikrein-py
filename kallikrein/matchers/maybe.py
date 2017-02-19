from typing import Union, TypeVar

from kallikrein.matchers.typed import have_type, ChainTyped
from kallikrein.matchers import contain
from kallikrein.matcher import StrictMatcher, BoundMatcher
from kallikrein.matchers.contain import PredContain

from amino import Maybe, Boolean, Just, Empty

A = TypeVar('A')
B = TypeVar('B')


class ChainTypedJust(ChainTyped, tpe=Just):

    def chain(self, matcher: StrictMatcher, other: Union[A, BoundMatcher]
              ) -> BoundMatcher:
        return matcher & contain(other)


class PredContainMaybe(PredContain, tpe=Maybe):

    def check(self, exp: Maybe[A], target: A) -> Boolean:
        return Boolean(exp.contains(target))


be_just = have_type(Just)
be_empty = have_type(Empty)

__all__ = ('be_just', 'be_empty')
