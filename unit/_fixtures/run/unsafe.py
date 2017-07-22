from amino import List

from kallikrein.expectation import Expectation
from kallikrein import unsafe_k
from kallikrein.matchers import greater_equal, contain
from kallikrein.util.string import green_check, red_cross, yellow


head = 'spec with unsafe expectations'
l1 = 'success'
l2 = 'failure'


class Unsafe:
    __doc__ = '''{}
    {} $success
    {} $failure
    '''.format(head, l1, l2)

    __unsafe__ = None

    def success(self) -> Expectation:
        unsafe_k(3).must(greater_equal(2))
        unsafe_k(List(3)).must(contain(greater_equal(2)))

    def failure(self) -> Expectation:
        unsafe_k(3).must(greater_equal(2))
        unsafe_k(List(1, 0)).must(contain(greater_equal(2)))


target_report_unsafe = '''{}
 {} {}
 {} {}
  unsafe spec failed:
   `List` does not match:
    {}
    {}
'''.format(head, green_check, l1, red_cross, l2, yellow('1 < 2'),
           yellow('0 < 2'))

__all__ = ('Unsafe',)
