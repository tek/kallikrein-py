from kallikrein import k
from kallikrein.matchers.typed import have_type

from amino import List, Just
from amino.test.spec_spec import Spec


class TypedSpec(Spec):

    def list(self) -> None:
        exp = k(List(2)).must(have_type(List))
        assert exp.evaluate.attempt.value.success
        exp = k(Just(2)).must(have_type(List))
        assert exp.evaluate.attempt.value.failure

__all__ = ('TypedSpec',)
