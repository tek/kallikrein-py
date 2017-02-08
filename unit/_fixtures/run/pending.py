from kallikrein import k, pending, Expectation


class PendingSpec:
    '''pending spec
    pending $pend
    active $active
    '''

    @pending
    def pend(self) -> Expectation:
        pass

    def active(self) -> Expectation:
        return k(1) == 1

__all__ = ('PendingSpec',)
