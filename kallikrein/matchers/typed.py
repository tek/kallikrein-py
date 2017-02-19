from typing import TypeVar

from kallikrein.matcher import Predicate, matcher, NestingUnavailable

from amino import Boolean

A = TypeVar('A')


class PredTyped(Predicate):
    pass


class PredTypedAny(PredTyped, pred=lambda a: True):

    def check(self, exp: A, tpe: type) -> Boolean:
        return Boolean(isinstance(exp, tpe))


success = '`{}` is a `{}`'
failure = '`{}` is not a `{}`'
typed = matcher('typed', success, failure, PredTyped, NestingUnavailable)
have_type = typed

__all__ = ('typed', 'have_type')
