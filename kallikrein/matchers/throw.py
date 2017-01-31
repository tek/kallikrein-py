from typing import Callable, Any

from kallikrein.matcher import Matcher, matcher
from kallikrein.match_result import (MatchResult, SimpleMatchResult,
                                     MultiLineMatchResult)
from kallikrein.util.string import indent

from amino import Either, _, Try, L, List
from amino.anon import lambda_str


class Throw(Matcher[Callable]):
    simple_success = '`{}` raised {}'
    simple_failure = '`{}` raised {} instead of `{}`'
    nested_success = '`{}` raised and:'
    nested_failure = '`{}` raised but:'
    nested_failure_not_raise = '`{}` did not raise'
    no_exception = 'no exception'

    def exception(self, exp: Callable) -> Either[Any, Exception]:
        return Try(exp).swap / _.cause

    def match(self, exp: Callable) -> MatchResult[Callable]:
        exc = self.exception(exp)
        result = exc.exists(L(isinstance)(_, self.target))
        name = exc / (lambda a: a.__class__.__name__)
        exp_repr = lambda_str(exp)
        exc_repr = name / '`{}`'.format | Throw.no_exception
        success = Throw.simple_success.format(exp_repr, exc_repr)
        failure = Throw.simple_failure.format(
            exp_repr, exc_repr, self.target.__name__
        )
        return SimpleMatchResult(result, success, failure)

    def match_nested(self, exp: Callable) -> MatchResult[Callable]:
        exp_repr = lambda_str(exp)
        exc = self.exception(exp)
        nested = exc / self.target
        result = nested.exists(_.success)
        success_pre = Throw.nested_success.format(exp_repr)
        no_nested = List('no nested message')
        success_nested = nested / _.success_message | no_nested
        success = indent(success_nested).cons(success_pre)
        failure_pre = (
            Throw.nested_failure
            if exc.present else
            Throw.nested_failure_not_raise
        ).format(exp_repr)
        failure_nested = nested / _.failure_message | no_nested
        failure = (
            indent(failure_nested).cons(failure_pre)
            if exc.present else
            List(failure_pre)
        )
        return MultiLineMatchResult(result, success, failure)


throw = matcher(Throw)

__all__ = ('throw', 'Throw')
