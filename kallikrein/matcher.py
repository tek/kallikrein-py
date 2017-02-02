import abc
from typing import Generic, TypeVar, Union, Callable, Any

from kallikrein.match_result import (MatchResult, SimpleMatchResult,
                                     ForAllMatchResult)

from amino import List, _, L

A = TypeVar('A')
B = TypeVar('B')


class Matcher(Generic[A], abc.ABC):

    def __init__(self, target: Union[A, 'Matcher']) -> None:
        self.target = target

    def evaluate(self, exp: A) -> MatchResult[A]:
        return (
            self.match_nested(exp, self.target)
            if isinstance(self.target, Matcher) else
            self.match(exp, self.target)
        )

    @abc.abstractmethod
    def match(self, exp: A, target: A) -> MatchResult[A]:
        ...

    @abc.abstractmethod
    def match_nested(self, exp: A, target: 'Matcher') -> MatchResult[A]:
        ...

    def __str__(self) -> str:
        return '{}({})'.format(self.__class__.__name__, self.target)


MatcherCtor = Callable[[Union[A, Matcher[A]]], Matcher[B]]


def matcher(ctor: MatcherCtor) -> MatcherCtor:
    def create(target: Union[A, Matcher[A]]) -> Matcher[B]:
        return ctor(target)
    return create

__all__ = ('Matcher', 'matcher')
