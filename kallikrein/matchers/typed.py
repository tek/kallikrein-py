from typing import TypeVar, Type, Union

from kallikrein.matcher import (Predicate, matcher, NestingUnavailable,
                                BoundMatcher, StrictMatcher, ChainMatcher)

from amino import Boolean
from amino.tc.base import TypeClass

A = TypeVar('A')


class Typed:
    pass


class ChainTyped(TypeClass):

    def chain(self, tpe: Type) -> BoundMatcher:
        ...


class ChainMatcherTyped(ChainMatcher, tpe=Typed):

    def chain(self, matcher: StrictMatcher, other: Union[A, BoundMatcher]
              ) -> BoundMatcher:
        return ChainTyped.fatal(matcher.target).chain(matcher, other)


class PredTyped(Predicate):
    pass


class PredTypedAny(PredTyped, pred=lambda a: True):

    def check(self, exp: A, tpe: type) -> Boolean:
        return Boolean(isinstance(exp, tpe))


success = '`{}` is a `{}`'
failure = '`{}` is not a `{}`'
typed = matcher(Typed, success, failure, PredTyped, NestingUnavailable)
have_type = typed

__all__ = ('typed', 'have_type')
