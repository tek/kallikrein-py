from amino.test import Spec
from amino import List, L, _

from kallikrein.matchers import greater_equal, forall
from kallikrein import k
from kallikrein.expectable import ExpectationFailed, unsafe_k
from kallikrein.matcher import Matcher


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
        failure = checker(self._fail)
        success = checker(self._success)
        assert not failure.success
        assert success.success

    def unsafe(self) -> None:
        checker = L(unsafe_k)(_).match(self._matcher)
        try:
            checker(List(1, 2, 7))
        except ExpectationFailed:
            pass
        else:
            assert False, 'unsafe matcher failure didn\'t raise'
        checker(List(5, 6, 7))

__all__ = ('MatcherSpec',)
