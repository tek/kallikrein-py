from typing import Sequence, Generic, TypeVar, Union
from difflib import SequenceMatcher

from hues import huestr

from amino import Boolean, _, L, List, __
from amino.list import Lists

from kallikrein.matcher import BoundMatcher, Predicate, Nesting, SimpleTCMatcherBase
from kallikrein.util.string import green_plus, red_minus
from kallikrein.match_result import MatchResult, ForAllMatchResult

A = TypeVar('A')
B = TypeVar('B')
Strs = Sequence[str]


class Lines:
    pass


class PredLines(Generic[A, B], Predicate[A, B]):
    pass


class NestLines(Generic[A, B], Nesting[A, B]):
    pass


is_seq = L(issubclass)(_, Sequence)


def to_str_seq(seq: Strs) -> Strs:
    return Lists.lines(seq) if isinstance(seq, str) else Lists.wrap(seq)


class PredLinesSeq(PredLines[Strs, Strs], pred=is_seq):

    def check(self, exp: Strs, target: Strs) -> Boolean:
        return Boolean(to_str_seq(exp) == to_str_seq(target))


class NestLinesSeq(NestLines[Strs, MatchResult[Strs]], pred=is_seq):

    def match(self, exp: Strs, target: BoundMatcher[str]) -> List[MatchResult[str]]:
        return Lists.wrap(to_str_seq(exp)) / target.evaluate

    def wrap(self, name: str, exp: Sequence, nested: MatchResult) -> MatchResult[Strs]:
        return ForAllMatchResult(str(self), exp, nested)


def lines_match(exp: List[str], target: List[str]) -> List[str]:
    return List('Lines are equal')

sep = huestr('---').yellow.colorized


def lines_mismatch(exp: List[str], target: List[str]) -> str:
    pad = len(str(len(exp)))
    def make(index: Union[str, int], inserted: bool, line: str) -> str:
        sign = green_plus if inserted else red_minus
        i = huestr(f'{index: >{pad}}').blue.colorized
        return f'{sign} {i} {line}'
    def replace(start: int, index: List[int], pre: List[str], post: List[str]) -> List[str]:
        return index.zip(pre, post).flat_map3(lambda i, a, b: List(make(i, False, a), make('', True, b)))
    def delete(start: int, index: List[int], pre: List[str], post: List[str]) -> List[str]:
        return index.zip(pre).map2(lambda i, a: make(i, False, a))
    def insert(start: int, index: List[int], pre: List[str], post: List[str]) -> List[str]:
        def format(h: str, t: List[str]) -> List[str]:
            return t.map(lambda a: make('', True, a)).cons(make(start, True, h))
        return post.detach_head.map2(format) | List()
    def format(tag: str, i1: int, i2: int, j1: int, j2: int) -> List[str]:
        handle = replace if tag == 'replace' else delete if tag == 'delete' else insert
        pre = exp[i1:i2]
        post = target[j1:j2]
        return handle(i1, Lists.range(i1, i2), pre, post)
    sm = SequenceMatcher(None, exp, target)
    r = List.wrap(sm.get_opcodes())
    diffs = r.filter(lambda a: a[0] != 'equal').map5(format).flat_map(__.cons(sep)).indent(1).drop(1)
    return diffs.cons('Lines differ:')


class HaveLines(SimpleTCMatcherBase):

    def __init__(self) -> None:
        super().__init__(Lines, PredLines, NestLines)

    def format(self, success: bool, exp: Strs, target: Strs) -> List[str]:
        handle = lines_match if success else lines_mismatch
        return handle(to_str_seq(exp), to_str_seq(target))

have_lines = HaveLines()

__all__ = ('have_lines',)
