from kallikrein import k, Expectation


class AllSpecsSpec:
    __all_specs__ = None

    def setup(self) -> None:
        self.a = 5

    def spec1(self) -> Expectation:
        return k(self.a) == self.a

    def spec2(self) -> Expectation:
        return k(1) == 1

__all__ = ('AllSpecsSpec',)
