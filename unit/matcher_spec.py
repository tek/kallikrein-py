from amino.test import Spec
from amino import List, L, _

from kallikrein.matchers import greater_equal, forall
from kallikrein import k
from kallikrein.expectable import ExpectationFailed, unsafe_k
from kallikrein.matcher import Matcher
from kallikrein.expectation import UnsafeExpectation


class MatcherSpec(Spec):

    @property
    def _matcher(self) -> Matcher:
        return forall(greater_equal(5))

    @property
    def _fail(self) -> List[int]:
        return List(1, 2, 7)

    @property
    def _success(self) -> List[int]:
        return List(5, 6, 7)

    def functional(self) -> None:
        checker = L(k)(_).match(self._matcher)
        failure = checker(self._fail).evaluate.attempt
        success = checker(self._success).evaluate.attempt
        assert failure.present
        assert not failure.value.success
        assert success.present
        assert success.value.success

    def unsafe(self) -> None:
        checker = L(unsafe_k)(_).match(self._matcher)
        try:
            checker(List(1, 2, 7))
        except ExpectationFailed:
            pass
        except Exception as e:
            msg = 'unsafe matcher failure raised wrong exception {}'
            assert False, msg.format(e)
        else:
            assert False, 'unsafe matcher failure didn\'t raise'
        try:
            exp = checker(List(5, 6, 7))
            assert isinstance(exp, UnsafeExpectation)
            result = exp.evaluate.attempt
            assert result.present
            assert result.value.success
        except ExpectationFailed as e:
            assert False, 'usafe matcher raised for success case: {}'.format(e)

__all__ = ('MatcherSpec',)
