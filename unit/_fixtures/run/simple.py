from amino import List

from kallikrein.match_result import MatchResult
from kallikrein.matchers import greater_equal, contain, forall
from kallikrein import k
from kallikrein.util.string import green_check, red_cross, yellow


class EmptySpec:
    pass

l1 = 'example specifications'
l2 = 'this test is simple'
l3 = 'simple spec'
l4 = 'these tests are nested'
l5 = 'successful nesting'
l6 = 'failed spec'
err = '`ac` does not contain `b`'


class Simple:
    __doc__ = '''{}

    {}
    {} $simple

    {}
    {} $nested
    {} $failure
    '''.format(l1, l2, l3, l4, l5, l6)

    def setup(self) -> None:
        self.a = 3

    def simple(self) -> MatchResult:
        return k(3).must(greater_equal(self.a))

    def nested(self) -> MatchResult:
        return k(List(1, 2, 3)).must(contain(greater_equal(self.a)))

    def failure(self) -> MatchResult:
        return k(List('abc', 'abc', 'ac')).must(forall(contain('b')))


target_report_template = '''{}

{}
 {} {}

{}
 {} {}
 {} {}
  some elements do not match: {}
'''
target_report = target_report_template.format(
    l1, l2, green_check, l3, l4, green_check, l5, red_cross, l6, yellow(err))

target_report_method = '''{}

{}
 {} {}

{}
'''.format(l1, l2, green_check, l3, l4)

__all__ = ('EmptySpec', 'Simple')
