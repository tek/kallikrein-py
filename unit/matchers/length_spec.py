from amino.test import Spec
from amino import List

from kallikrein import k
from kallikrein.matchers.length import have_length
from kallikrein.expectation import Expectation
from kallikrein.match_result import MatchResult
from kallikrein.matchers import greater_equal


class LengthSpec(Spec):

    def _run(self, exp: Expectation, success: bool) -> MatchResult:
        expectation = exp.evaluate.attempt
        assert expectation.is_right
        result = expectation.value
        assert result.success == success
        return result

    def success(self) -> None:
        self._run(k(List(2, 3, 4)).must(have_length(3)), True)

    def failure(self) -> None:
        self._run(k(List(3, 4)).must(have_length(3)), False)

    def wrong_type(self) -> None:
        result = self._run(k(3).must(have_length(3)), False)
        assert 'has no length' in result.report

    def success_nested(self) -> None:
        self._run(k(List(2, 3, 4)).must(have_length(greater_equal(2))), True)

    def failure_nested(self) -> None:
        self._run(k(List(2, 3, 4)).must(have_length(greater_equal(4))), False)

__all__ = ('LengthSpec',)
