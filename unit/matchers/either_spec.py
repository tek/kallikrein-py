from amino.test import Spec
from amino import Right, Left, List

from kallikrein import k
from kallikrein.matchers.either import be_right, be_left
from kallikrein.match_result import MatchResult
from kallikrein.expectation import Expectation
from kallikrein.matchers import contain


class EitherSpec(Spec):

    def _run(self, exp: Expectation, success: bool, count: int = 1
             ) -> MatchResult:
        expectation = exp.evaluate.attempt
        assert expectation.is_right
        result = expectation.value
        assert result.success == success
        assert len(result.report_lines) == count
        return result

    def success_right(self) -> None:
        result = self._run(k(Right(1)).must(be_right), True)
        assert 'not' not in result.report

    def success_left(self) -> None:
        result = self._run(k(Left(1)).must(be_left), True)
        assert 'not' not in result.report

    def failure(self) -> None:
        result = self._run(k(Left(1)).must(be_right), False)
        assert 'not' in result.report

    def value_success(self) -> None:
        result = self._run(k(Right(1)).must(be_right(1)), True, 2)
        assert 'not' not in result.report

    def value_failure(self) -> None:
        self._run(k(Right(1)).must(be_right(2)), False)

    def value_and_type_failure(self) -> None:
        self._run(k(Left(1)).must(be_right(2)), False, 2)

    def nested_success(self) -> None:
        self._run(k(Right(List(1, 2))).must(be_right(contain(2))), True, 2)

    def nested_failure(self) -> None:
        self._run(k(Right(List(1, 3))).must(be_right(contain(2))), False)

__all__ = ('EitherSpec',)
