from amino.test.spec_spec import Spec
from amino import List, Just, Empty

from kallikrein import k
from kallikrein.match_result import MatchResult
from kallikrein.expectation import Expectation
from kallikrein.matchers import contain
from kallikrein.matchers.maybe import be_just, be_empty


class MaybeSpec(Spec):

    def _run(self, exp: Expectation, success: bool, count: int = 1
             ) -> MatchResult:
        expectation = exp.evaluate.attempt
        assert expectation.is_right
        result = expectation.value
        assert result.success == success
        assert len(result.report_lines) == count
        return result

    def success_just(self) -> None:
        result = self._run(k(Just(1)).must(be_just(1)), True, 2)
        assert 'not' not in result.report

    def success_empty(self) -> None:
        result = self._run(k(Empty()).must(be_empty), True)
        assert 'not' not in result.report

    def failure(self) -> None:
        result = self._run(k(Empty()).must(be_just), False)
        assert 'not' in result.report

    def nested_success(self) -> None:
        self._run(k(Just(List(1, 2))).must(be_just(contain(2))), True, 2)

    def nested_failure(self) -> None:
        self._run(k(Just(List(1, 3))).must(be_just(contain(2))), False)

__all__ = ('MaybeSpec',)
