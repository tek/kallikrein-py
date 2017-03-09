from amino.test.spec_spec import Spec
from amino import Right, Left

from kallikrein import k
from kallikrein.expectation import Expectation
from kallikrein.match_result import MatchResult
from kallikrein.matchers.typed import have_type
from kallikrein.matchers.either import ChainTypedEither  # NOQA


class ChainSpec(Spec):

    def _run(self, exp: Expectation, success: bool) -> MatchResult:
        expectation = exp.evaluate.attempt
        assert expectation.is_right
        result = expectation.value
        assert result.success == success
        return result

    def success(self) -> None:
        self._run(k(Right(5)).must(have_type(Right)(5)), True)

    def failure(self) -> None:
        self._run(k(Left(5)).must(have_type(Right)(5)), False)

__all__ = ('ChainSpec',)
