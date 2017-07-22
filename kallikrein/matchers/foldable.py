from typing import Union, TypeVar

from kallikrein.matchers.typed import ChainTyped
from kallikrein.matchers import contain
from kallikrein.matcher import StrictMatcher, BoundMatcher
from kallikrein.matchers.contain import PredContain

from amino import Boolean
from amino.tc.foldable import Foldable

A = TypeVar('A')
B = TypeVar('B')


class ChainTypedFoldable(ChainTyped, dep=[Foldable]):

    def chain(self, matcher: StrictMatcher, other: Union[A, BoundMatcher]
              ) -> BoundMatcher:
        return matcher & contain(other)


class PredContainFoldable(PredContain, dep=[Foldable]):

    def check(self, exp: A, target: B) -> Boolean:
        return Boolean(Foldable.fatal_for(exp).contains(target))

__all__ = ('ChainTypedFoldable', 'PredContainFoldable')
