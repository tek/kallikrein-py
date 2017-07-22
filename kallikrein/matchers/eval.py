from typing import TypeVar, Generic

from kallikrein.matcher import Predicate, matcher, BoundMatcher, Nesting
from kallikrein.match_result import MatchResult

from amino import Boolean, Eval

A = TypeVar('A')
B = TypeVar('B')


class EvalTo:
    pass


class PredEvalTo(Predicate):
    pass


class NestEvalTo(Generic[A, B], Nesting[Eval[A], B]):
    pass


class PredEvalToEval(PredEvalTo, tpe=Eval):

    def check(self, exp: Eval[A], target: A) -> Boolean:
        return Boolean(exp._value() == target)


# FIXME need NestedMatchResult
class NestEvalToEval(Generic[A], NestEvalTo[A, MatchResult[A]], tpe=Eval):

    def match(self, exp: Eval[A], target: BoundMatcher[A]) -> MatchResult[A]:
        return target.evaluate(exp._value())

    def wrap(self, name: str, exp: Eval[A], nested: MatchResult[A]) -> MatchResult[A]:
        return nested


success = '`{}` evaluates to `{}`'
failure = '`{}` does not evaluate to `{}`'
eval_to = matcher(EvalTo, success, failure, PredEvalTo, NestEvalTo)

__all__ = ('eval_to',)
