from typing import Callable, Any

from kallikrein.matcher import Matcher
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

    def match(self, exp: Callable, target: type) -> MatchResult[Callable]:
        exc = self.exception(exp)
        result = exc.exists(L(isinstance)(_, target))
        name = exc / (lambda a: a.__class__.__name__)
        exp_repr = lambda_str(exp)
        exc_repr = name / '`{}`'.format | Throw.no_exception
        message = (
            Throw.simple_success.format(exp_repr, exc_repr)
            if result else
            Throw.simple_failure.format(exp_repr, exc_repr, target.__name__)
        )
        return SimpleMatchResult(result, message)

    def match_nested(self, exp: Callable, target: Matcher
                     ) -> MatchResult[Callable]:
        exp_repr = lambda_str(exp)
        exc = self.exception(exp)
        nested = exc / target.evaluate
        result = nested.exists(_.success)
        success_pre = Throw.nested_success.format(exp_repr)
        no_nested = List('no nested message')
        success_nested = nested / _.message | no_nested
        success = indent(success_nested).cons(success_pre)
        failure_pre = (
            Throw.nested_failure
            if exc.present else
            Throw.nested_failure_not_raise
        ).format(exp_repr)
        failure_nested = nested / _.message | no_nested
        failure = (
            indent(failure_nested).cons(failure_pre)
            if exc.present else
            List(failure_pre)
        )
        message = success if result else failure
        return MultiLineMatchResult(result, message)


throw = Throw()

__all__ = ('throw', 'Throw')
