from typing import Union

from amino.test.spec_spec import Spec
from amino import Right, List, Eval
from amino.list import Lists

from kallikrein import k, Expectation
from kallikrein.matchers.either import be_right
from kallikrein.matchers.lines import have_lines
from kallikrein.matchers.eval import eval_to
from kallikrein.util.string import blue, yellow, green_plus, red_minus


text = 'first line\nsecond line\nthird line\nfourth line\nfifth line'
lines = Lists.lines(text)

success_target = '''`Right([first line, second line, third line, fourth line, fifth line])` is a `amino.either.Right`
Contain succeeded: Lines are equal'''

line1 = f' {red_minus} {blue(1)} second line'
line2 = f' {red_minus} {blue(3)} fourth line'
line3 = f' {green_plus} {blue(5)} sixth line'


class EvalSpec(Spec):

    def _run(self, target: Union[List[str], str]) -> Expectation:
        def f(t: str) -> List[str]:
            return Eval.later(Lists.lines, t).map(Right)
        exp = k(Eval.now(text).flat_map(f)).must(eval_to(be_right(have_lines(target))))
        res = exp.evaluate.attempt
        assert isinstance(res, Right)
        return res.value

    def success(self) -> None:
        res = self._run(text)
        assert res.report == success_target

    # FIXME positive match on Right's type not displayed
    def failure(self) -> None:
        target = List(lines[0], lines[2], 'forth lane', lines[4], 'sixth line')
        res = self._run(target)
        assert res.report_lines[2] == ' ' + yellow(line1)
        assert res.report_lines[4] == ' ' + yellow(line2)
        assert res.report_lines[7] == ' ' + yellow(line3)

__all__ = ('EvalSpec',)
