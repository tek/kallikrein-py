from amino.test import Spec
from amino import List, Right, Left

from kallikrein.run.main import runners, specs_run_task
from kallikrein import k
from kallikrein.matchers import greater_equal, contain, forall
from kallikrein.match_result import MatchResult
from kallikrein.run.line import SpecLine


class RunSpec(Spec):

    @property
    def specs(self) -> List[str]:
        return List('unit.run_spec._Simple')

    def runners(self) -> None:
        result = runners(self.specs)
        result.should.be.right
        assert len(result.value) == 1
        runner = result.value[0]
        assert runner.spec_cls == _Simple
        lines = runner.lines
        assert len(lines) == 9
        assert len(lines.filter_type(SpecLine)) == 3

    def run(self) -> None:
        task = specs_run_task(self.specs)
        result = task.attempt
        assert isinstance(result, Right)
        assert result.value.report == target_report

    def no_docstring(self) -> None:
        result = specs_run_task(List('unit.run_spec._Empty'))
        assert isinstance(result.attempt, Left)


class _Empty:
    pass

l1 = 'example specifications'
l2 = 'this test is simple'
l3 = 'simple spec'
l4 = 'these tests are nested'
l5 = 'successful nesting'
l6 = 'failed spec'


class _Simple:
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


checkmark = '\x1b[32m✓\x1b[0m'
target_report_template = '''{}

{}
 {} {}

{}
 {} {}
 \x1b[31m✗\x1b[0m {}
  some elements do not match:
   \x1b[33m`ac` does not contain `b`\x1b[0m
'''
target_report = target_report_template.format(l1, l2, checkmark, l3, l4,
                                              checkmark, l5, l6)

__all__ = ('RunSpec',)
