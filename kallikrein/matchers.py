import abc
import operator
from typing import Generic, TypeVar, List, Tuple, Callable, Union
from numbers import Number

from kallikrein.match_result import (MatchResult, SimpleMatchResult,
                                     BadNestedMatch, ExistsMatchResult,
                                     ForAllMatchResult)
from kallikrein.matcher import Matcher, matcher, MatcherCtor
from amino import Boolean, L, _

A = TypeVar('A')


class Contain(Generic[A], Matcher[List[A]]):

    def match(self, exp: List[A]) -> MatchResult[List[A]]:
        success = '`{}` contains `{}`'.format(exp, self.target)
        failure = '`{}` does not contain `{}`'.format(exp, self.target)
        return SimpleMatchResult(Boolean(self.target in exp), success, failure)

    def match_nested(self, exp: List[A]) -> MatchResult[List[A]]:
        nested = exp / self.target
        return ExistsMatchResult(str(self), exp, nested)


contain = matcher(Contain)


class ForAll(Generic[A], Matcher[List[A]]):

    def match(self, exp: List[A]) -> MatchResult[List[A]]:
        success = 'all elements of {} are == {}'.format(exp, self.target)
        failure = 'some elements of {} are /= {}'.format(exp, self.target)
        return SimpleMatchResult(self.target in exp, success, failure)

    def match_nested(self, exp: List[A]) -> MatchResult[List[A]]:
        nested = exp / self.target
        return ForAllMatchResult(str(self), exp, nested)


forall = matcher(ForAll)


class Comparison(Matcher[Number]):

    @abc.abstractproperty
    def operator(self) -> Callable[[Number, Number], Boolean]:
        ...

    @abc.abstractproperty
    def operator_reprs(self) -> Tuple[str, str]:
        ...

    def match(self, exp: Number) -> MatchResult[Number]:
        op_s, op_f = self.operator_reprs
        success = '{} {} {}'.format(exp, op_s, self.target)
        failure = '{} {} {}'.format(exp, op_f, self.target)
        result = Boolean(self.operator(exp, self.target))
        return SimpleMatchResult(result, success, failure)

    def match_nested(self) -> MatchResult[Number]:
        return BadNestedMatch(self)


class SimpleComparison(Comparison):

    def __init__(self, op: Callable[[Number, Number], bool], op_s: str,
                 op_f: str, target: Union[A, 'Matcher[A]']) -> None:
        super().__init__(target)
        self.op = op
        self.op_s = op_s
        self.op_f = op_f

    @property
    def operator(self) -> Callable[[Number, Number], Boolean]:
        return L(self.op)(_, _) >> Boolean

    @property
    def operator_reprs(self) -> Tuple[str, str]:
        return self.op_s, self.op_f


def comparison(op: Callable[[Number, Number], bool], op_s: str, op_f: str
               ) -> MatcherCtor:
    return matcher(L(SimpleComparison)(op, op_s, op_f, _))

equal = eq = comparison(operator.eq, '==', '/=')
greater_equal = ge = comparison(operator.ge, '>=', '<')

__all__ = ('Contain', 'contain', 'greater_equal', 'equal', 'ge', 'eq',
           'forall')
