from amino.test import Spec
from amino import List

from kallikrein import k
from kallikrein.matchers.length import have_length
from kallikrein.expectation import Expectation
from kallikrein.match_result import MatchResult
from kallikrein.matchers import contain
from kallikrein.matchers.contain import failure as contain_failure
from kallikrein.matchers.typed import have_type


class AlgSpec(Spec):

    def _run(self, exp: Expectation, success: bool) -> MatchResult:
        expectation = exp.evaluate.attempt
        assert expectation.is_right
        result = expectation.value
        assert result.success == success
        return result

    def success(self) -> None:
        self._run(k(List(2, 3, 4)).must(have_length(3) & contain(4)), True)

    def failure(self) -> None:
        exp = List(2, 3, 4)
        n = 5
        mathers = have_length(3) & have_type(List) & contain(n)
        result = self._run(k(exp).must(mathers), False)
        assert result.report == contain_failure.format(exp, n)

__all__ = ('AlgSpec',)
