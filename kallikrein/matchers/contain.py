from typing import TypeVar
from typing import Collection  # type: ignore
from collections.abc import Container, Iterable

from amino import Boolean, List, L, _

from kallikrein.matcher import Predicate, Nesting, matcher, BoundMatcher
from kallikrein.match_result import (MatchResult,
                                     ExistsMatchResult)

A = TypeVar('A')
B = TypeVar('B')


class Contain:
    pass


class PredContain(Predicate):
    pass


class NestContain(Nesting):
    pass


is_container = L(issubclass)(_, Container)
is_collection = L(issubclass)(_, Iterable)


class PredContainCollection(PredContain, pred=is_container):

    def check(self, exp: Collection[A], target: A) -> Boolean:
        return Boolean(target in exp)


class NestContainCollection(NestContain, pred=is_collection):

    def match(self, exp: Collection[A], target: BoundMatcher
              ) -> List[MatchResult[B]]:
        return List.wrap([target.evaluate(e) for e in exp])

    def wrap(self, name: str, exp: Collection[A], nested: List[MatchResult[B]]
             ) -> MatchResult[A]:
        return ExistsMatchResult(name, exp, nested)


success = '`{}` contains `{}`'
failure = '`{}` does not contain `{}`'
contain = matcher(Contain, success, failure, PredContain, NestContain)

__all__ = ('contain',)
