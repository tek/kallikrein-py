import abc
from typing import Generic, TypeVar, Union, Callable

from kallikrein.match_result import MatchResult

A = TypeVar('A')
B = TypeVar('B')


class Matcher(Generic[A], abc.ABC):

    def __init__(self, target: Union[A, 'Matcher[A]']) -> None:
        self.target = target

    def __call__(self, exp: Union[A, 'Matcher[B]']
                 ) -> Union[MatchResult[A], MatchResult[B]]:
        return (
            self.match_nested(exp)  # type: ignore
            if isinstance(self.target, Matcher) else
            self.match(exp)  # type: ignore
        )

    @abc.abstractmethod
    def match(self, exp: Union[A, 'Matcher[B]']
              ) -> Union[MatchResult[A], MatchResult[B]]:
        ...

    @abc.abstractmethod
    def match_nested(self, exp: 'Matcher[B]') -> MatchResult[B]:
        ...

    def __str__(self) -> str:
        return '{}({})'.format(self.__class__.__name__, self.target)


MatcherCtor = Callable[[Union[A, Matcher[A]]], Matcher[B]]


def matcher(ctor: MatcherCtor) -> MatcherCtor:
    def create(target: Union[A, Matcher[A]]) -> Matcher[B]:
        return ctor(target)
    return create

__all__ = ('Matcher', 'matcher')
