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

    def __call__(self, exp: A) -> MatchResult[A]:
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


class TrueMatcher(Matcher[Any]):

    def __init__(self) -> None:
        super().__init__(True)

    def match(self, exp: Any, target: Any) -> MatchResult[Any]:
        return SimpleMatchResult(True, 'true', 'true')

    def match_nested(self, exp: Any, target: Matcher) -> MatchResult[Any]:
        return SimpleMatchResult(True, 'true', 'true')


class TypedMatcher(Generic[A], Matcher[A]):
    success = '`{}` is a `{}`'
    failure = '`{}` is not a `{}`'

    def __init__(self, tpe: type, target: Union[A, Matcher]) -> None:
        super().__init__(target)
        self.tpe = tpe

    def match(self, exp: A, target: A) -> MatchResult[A]:
        succ = TypedMatcher.success.format(exp, self.tpe)
        fail = TypedMatcher.failure.format(exp, self.tpe)
        return SimpleMatchResult(isinstance(exp, self.tpe), succ, fail)

    def match_nested(self, exp: A, target: Matcher) -> MatchResult[A]:
        return ForAllMatchResult('typed', exp,
                                 List(self.match(exp, exp), target(exp)))


def typed(tpe: type, nested: Matcher) -> Matcher:
    return matcher(L(TypedMatcher)(tpe, _))(nested)


def have_type(tpe: type) -> Matcher:
    return typed(tpe, TrueMatcher())

__all__ = ('Matcher', 'matcher', 'TypedMatcher')
