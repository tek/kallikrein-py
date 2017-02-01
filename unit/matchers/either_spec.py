from amino.test import Spec
from amino import Right, Left

from kallikrein import k
from kallikrein.matchers.either import be_right


class EitherSpec(Spec):

    def success(self) -> None:
        result = k(Right(1)).must(be_right)
        assert result.evaluate.attempt.value.success

    def failure(self) -> None:
        result = k(Left(1)).must(be_right)
        assert result.evaluate.attempt.value.failure

__all__ = ('EitherSpec',)
