import abc
import operator
from typing import Tuple, Callable
from numbers import Number

from kallikrein.match_result import (MatchResult, SimpleMatchResult,
                                     BadNestedMatch)
from kallikrein.matcher import Matcher, BoundMatcher
from amino import Boolean, L, _


class Comparison(Matcher[Number]):

    @abc.abstractproperty
    def operator(self) -> Callable[[Number, Number], Boolean]:
        ...

    @abc.abstractproperty
    def operator_reprs(self) -> Tuple[str, str]:
        ...

    def match(self, exp: Number, target: Number) -> MatchResult[Number]:
        result = Boolean(self.operator(exp, target))
        op_s, op_f = self.operator_reprs
        op = op_s if result else op_f
        message = '{} {} {}'.format(exp, op, target)
        return SimpleMatchResult(result, message)

    def match_nested(self, exp: Number, target: BoundMatcher) -> MatchResult[Number]:
        return BadNestedMatch(self)


class SimpleComparison(Comparison):

    def __init__(self, op: Callable[[Number, Number], bool], op_s: str,
                 op_f: str) -> None:
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
               ) -> Matcher[Number]:
    return SimpleComparison(op, op_s, op_f)

equal = comparison(operator.eq, '==', '/=')
eq = equal

not_equal = comparison(operator.ne, '/=', '==')
ne = not_equal

greater_equal = comparison(operator.ge, '>=', '<')
ge = greater_equal

greater = comparison(operator.gt, '>', '<=')
gt = greater

less_equal = comparison(operator.le, '<=', '>')
le = less_equal

less = comparison(operator.lt, '<', '>=')
lt = less

__all__ = ('equal', 'greater_equal', 'eq', 'ge', 'greater', 'gt', 'less_equal',
           'le', 'less', 'lt')
