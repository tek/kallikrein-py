from amino.test.spec_spec import Spec

from kallikrein import k
from kallikrein.match_result import MatchResult
from kallikrein.expectation import Expectation
from kallikrein.matchers import contain
from kallikrein.matchers.comparison import greater


def _run(exp: Expectation, success: bool) -> MatchResult:
    expectation = exp.evaluate.attempt
    assert expectation.is_right
    result = expectation.value
    assert result.success == success


class ContainSpec(Spec):

    def success(self) -> None:
        _run(k([1, 9]).must(contain(greater(5))), True)

    def failure(self) -> None:
        _run(k([1, 9]).must(contain(greater(10))), False)

__all__ = ('ContainSpec',)
