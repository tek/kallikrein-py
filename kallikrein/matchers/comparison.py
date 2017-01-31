import abc
import operator
from typing import Tuple, Callable, Union
from numbers import Number

from kallikrein.match_result import (MatchResult, SimpleMatchResult,
                                     BadNestedMatch)
from kallikrein.matcher import Matcher, matcher, MatcherCtor
from amino import Boolean, L, _


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
                 op_f: str, target: Union[Number, 'Matcher[Number]']) -> None:
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

__all__ = ('equal', 'greater_equal')
