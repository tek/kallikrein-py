import abc
from typing import Generic, TypeVar, Union, Callable, Type

from kallikrein.match_result import (MatchResult, SimpleMatchResult,
                                     BadNestedMatch)

from amino import Boolean, Maybe, List, _, __
from amino.tc.base import TypeClass

A = TypeVar('A')
B = TypeVar('B')
C = TypeVar('C')


class MatcherAlg:

    @abc.abstractmethod
    def __and__(self, other: 'MatcherAlg') -> 'MatcherAlg':
        ...

    @abc.abstractmethod
    def __or__(self, other: 'MatcherAlg') -> 'MatcherAlg':
        ...


class MatchResultAlg(MatchResult[List[A]], Generic[A]):

    def __init__(self, sub: List[MatchResult]) -> None:
        self.sub = sub

    @property
    def failures(self) -> List[MatchResult]:
        return self.sub.filter(_.failure)

    @property
    def message(self) -> List[str]:
        return (
            self.sub // _.message
            if self.success else
            self.failures // _.message
        )


class MatchResultAnd(MatchResultAlg):

    @property
    def success(self) -> Boolean:
        return self.sub.forall(_.success)


class MatchResultOr(MatchResultAlg):

    @property
    def success(self) -> Boolean:
        return self.sub.exists(_.success)


class BoundMatcher(Generic[A], MatcherAlg):

    @abc.abstractmethod
    def evaluate(self, exp: A) -> MatchResult[A]:
        ...

    def __and__(self, other: MatcherAlg) -> MatcherAlg:
        return BoundMatcherAlg(List(self, other), MatchResultAnd)

    def __or__(self, other: MatcherAlg) -> MatcherAlg:
        return BoundMatcherAlg(List(self, other), MatchResultOr)


class SimpleBoundMatcher(BoundMatcher[A], Generic[A, B]):

    def __init__(self, matcher: Callable[[A, B], MatchResult], target: B
                 ) -> None:
        self.matcher = matcher
        self.target = target

    def __str__(self) -> str:
        return '{}({}, {})'.format(self.__class__.__name__, self.matcher,
                                   self.target)

    def evaluate(self, exp: A) -> MatchResult[A]:
        return self.matcher(exp, self.target)


class StrictMatcher(SimpleBoundMatcher[A, A], Generic[A]):
    pass


class NestedMatcher(SimpleBoundMatcher[A, SimpleBoundMatcher], Generic[A]):
    pass


class BoundMatcherAlg(BoundMatcher[A], Generic[A, B]):

    def __init__(self, sub: List[SimpleBoundMatcher[A, B]],
                 result_ctor: Type[MatchResultAlg]) -> None:
        self.sub = sub
        self.result_ctor = result_ctor

    def evaluate(self, exp: A) -> MatchResult[A]:
        return self.result_ctor(self.sub.map(__.evaluate(exp)))


class Matcher(Generic[A]):

    def __call__(self, target: Union[A, SimpleBoundMatcher]
                 ) -> SimpleBoundMatcher:
        if isinstance(target, SimpleBoundMatcher):
            return NestedMatcher(self.match_nested, target)
        else:
            return StrictMatcher(self.match, target)

    @abc.abstractmethod
    def match(self, exp: A, target: A) -> MatchResult[A]:
        ...

    @abc.abstractmethod
    def match_nested(self, exp: A, target: SimpleBoundMatcher
                     ) -> MatchResult[A]:
        ...


class Predicate(TypeClass):

    @abc.abstractmethod
    def check(exp: A, target: B) -> Boolean:
        ...


class Nesting(TypeClass):

    @abc.abstractmethod
    def match(self, exp: A, target: SimpleBoundMatcher) -> C:
        ...

    @abc.abstractmethod
    def wrap(self, name: str, exp: A, nested: C) -> MatchResult:
        ...


class NestingUnavailable(Nesting):

    def match(self, exp: A, target: SimpleBoundMatcher) -> C:
        return BadNestedMatch(self.tpe)

    def wrap(self, name: str, exp: A, nested: C) -> MatchResult:
        return BadNestedMatch(self.tpe)


class NestingUnavailableAny(NestingUnavailable, pred=lambda a: True):
    pass


class NoInstance(Exception):

    def __init__(self, pred: type, exp: A) -> None:
        msg = 'no {} defined for {}'.format(pred.__name__, exp)
        super().__init__(msg)


class TCMatcher(Matcher[A]):

    @abc.abstractproperty
    def pred_tc(self) -> Type[Predicate]:
        ...

    @abc.abstractproperty
    def nest_tc(self) -> Type[Nesting]:
        ...

    @abc.abstractmethod
    def format(self, success: bool, exp: A, target: B) -> str:
        ...

    def pred(self, exp: A, target: B) -> Maybe[Predicate]:
        return self.pred_tc.m_for(exp)

    def pred_fatal(self, exp: A, target: B) -> Predicate:
        return (
            self.pred_tc.m_for(exp)
            .get_or_raise(NoInstance(self.pred_tc, exp))
        )

    def check_pred(self, exp: A, target: B) -> Boolean:
        return (
            self.pred_fatal(exp, target)  # type: ignore
            .check(exp, target)
        )

    def nest(self, exp: A) -> Nesting:
        return (
            self.nest_tc.m(type(exp))
            .get_or_raise(NoInstance(self.nest_tc, exp))
        )

    def match(self, exp: A, target: B) -> MatchResult[A]:
        success = self.check_pred(exp, target)
        message = self.format(success, exp, target)
        return SimpleMatchResult(success, message)

    def match_nested(self, exp: A, target: SimpleBoundMatcher
                     ) -> MatchResult[A]:
        nest = self.nest(exp)
        nested = nest.match(exp, target)
        return nest.wrap(self.name, exp, nested)


class SimpleTCMatcher(TCMatcher):

    def __init__(self, name: str, success_tmpl: str, failure_tmpl: str,
                 pred_tc: Type[Predicate], nest_tc: Type[Nesting]) -> None:
        self.name = name
        self.success_tmpl = success_tmpl
        self.failure_tmpl = failure_tmpl
        self._pred_tc = pred_tc
        self._nest_tc = nest_tc

    def format(self, success: bool, exp: A, target: B) -> str:
        tmpl = self.success_tmpl if success else self.failure_tmpl
        return tmpl.format(exp, target)

    @property
    def pred_tc(self) -> Type[Predicate]:
        return self._pred_tc

    @property
    def nest_tc(self) -> Type[Nesting]:
        return self._nest_tc

matcher = SimpleTCMatcher

__all__ = ('Matcher', 'BoundMatcher', 'Predicate', 'Nesting', 'NoInstance',
           'TCMatcher', 'SimpleTCMatcher', 'BoundMatcher')
