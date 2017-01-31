from amino.test import Spec
from amino import List

from kallikrein import k
from kallikrein.matchers import contain


class MultiSpec(Spec):

    def and_success(self) -> None:
        l = List(1, 2, 3)
        exp = (k(l).must(contain(1)) & k(l).must(contain(2)) &
               k(l).must(contain(3)))
        result = exp.evaluate.attempt
        assert result.present
        assert result.value.success

    def and_failure(self) -> None:
        l = List(1, 2, 3)
        exp = (k(l).must(contain(1)) & k(l).must(contain(2)) &
               k(l).must(contain(4)))
        result = exp.evaluate.attempt
        assert result.present
        assert result.value.failure

    def or_success(self) -> None:
        l = List(1, 2, 3)
        exp = k(l).must(contain(4)) | k(l).must(contain(2))
        result = exp.evaluate.attempt
        assert result.value.success

    def or_failure(self) -> None:
        l = List(1, 2, 3)
        exp = k(l).must(contain(4)) | k(l).must(contain(5))
        result = exp.evaluate.attempt
        assert result.value.failure

    def mixed_success(self) -> None:
        l = List(1, 2, 3)
        exp = (k(l).must(contain(4)) | k(l).must(contain(3)) &
               k(l).must(contain(2)))
        result = exp.evaluate.attempt
        assert result.value.success

    def mixed_failure(self) -> None:
        l = List(1, 2, 3)
        exp = (k(l).must(contain(4)) | k(l).must(contain(3)) &
               k(l).must(contain(5)))
        result = exp.evaluate.attempt
        assert result.value.failure

__all__ = ('MultiSpec',)
