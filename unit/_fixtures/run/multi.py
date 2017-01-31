from amino import List

from kallikrein.expectation import Expectation
from kallikrein import k
from kallikrein.matchers import greater_equal, contain


class Multi:
    __doc__ = '''spec with multiple expectations
    multi $multi
    '''

    def multi(self) -> Expectation:
        return (k(3).must(greater_equal(2)) &
                k(List(3)).must(contain(greater_equal(2))))

__all__ = ('Multi',)
