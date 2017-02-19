import abc
from typing import Generic, TypeVar, Any

from hues import huestr

from amino import Boolean, List, _
from amino.boolean import false

from kallikrein.util.string import indent

A = TypeVar('A')
B = TypeVar('B')


class MatchResult(Generic[A]):

    @abc.abstractproperty
    def success(self) -> Boolean:
        ...

    @property
    def failure(self) -> Boolean:
        return not self.success

    @abc.abstractproperty
    def message(self) -> List[str]:
        ...

    @property
    def report_lines(self) -> List[str]:
        return self.message

    @property
    def report(self) -> str:
        return self.report_lines.join_lines

    def __str__(self) -> str:
        return '{}({})'.format(self.__class__.__name__, self.report)


class SimpleMatchResult(Generic[A], MatchResult[A]):

    def __init__(self, result: bool, msg: str) -> None:
        self.result = Boolean(result)
        self.msg = msg

    @property
    def success(self) -> Boolean:
        return self.result

    @property
    def message(self) -> List[str]:
        return List(self.msg)


class MultiLineMatchResult(Generic[A], MatchResult[A]):

    def __init__(self, result: bool, msg: List[str]) -> None:
        self.result = Boolean(result)
        self.msg = msg

    @property
    def success(self) -> Boolean:
        return self.result

    @property
    def message(self) -> List[str]:
        return self.msg


class NestedMatchResultBase(MatchResult):

    def __init__(self, exp: A, nested: List[MatchResult]) -> None:
        self.exp = exp
        self.nested = nested

    @abc.abstractproperty
    def main_message(self) -> str:
        ...

    @abc.abstractproperty
    def main_message_concat(self) -> str:
        ...

    @property
    def message(self) -> List[str]:
        n = self.nested_messages
        m = self.main_message_concat
        return (List('{} {}'.format(m, n.mk_string()))
                if n.length == 1 else
                indent(n).cons(m))

    @property
    def failures(self) -> List[MatchResult]:
        return self.nested.filter_not(_.success)

    @property
    def nested_success(self) -> bool:
        return self.failures.empty

    @property
    def nested_messages(self) -> List[str]:
        n = self.nested if self.nested_success else self.failures
        msgs = n / _.report
        return (msgs
                if self.nested_success else
                msgs / huestr / _.yellow.colorized)


# TODO allow empty nested list, in which case omit from message
# use this instead of passing `SuccessMatchResult`
class NestedMatchResult(NestedMatchResultBase):

    def __init__(self, exp: A, main_success: bool, main_msg: str,
                 nested: List[MatchResult]) -> None:
        super().__init__(exp, nested)
        self.main_success = Boolean(main_success)
        self.main_msg = main_msg

    @property
    def main_message(self) -> str:
        return self.main_msg

    @property
    def main_message_concat(self) -> str:
        conj = ('but'
                if self.main_success and not self.nested_success else
                'and')
        return '{} {}'.format(self.main_msg, conj)

    @property
    def failure_message(self) -> str:
        return self.main_msg

    @property
    def success(self) -> Boolean:
        return self.main_success and self.nested_success


class MultiMatchResult(NestedMatchResultBase):
    success_message_template = '{} succeeded:'

    def __init__(self, desc: str, exp: A, nested: List[MatchResult]) -> None:
        super().__init__(exp, nested)
        self.desc = desc

    @property
    def main_message(self) -> List[str]:
        return self.success_message if self.success else self.failure_message

    main_message_concat = main_message

    @property
    def success_message(self) -> str:
        return self.success_message_template.format(self.desc)

    @property
    def failure_message(self) -> str:
        return 'multi match failed for:'


class ExistsMatchResult(MultiMatchResult):

    @property
    def success(self) -> Boolean:
        return self.nested.exists(_.success)

    @property
    def failure_message(self) -> List[str]:
        return 'no elements match'


class ForAllMatchResult(MultiMatchResult):

    @property
    def success(self) -> Boolean:
        return self.failures.empty

    @property
    def failure_message(self) -> List[str]:
        return 'some elements do not match:'


class BadNestedMatch(MatchResult[Any]):

    def __init__(self, matcher: Any) -> None:
        self.matcher = matcher

    @property
    def success(self) -> Boolean:
        return false

    @property
    def message(self) -> List[str]:
        return List('`{}` cannot take nested matchers')


class SuccessMatchResult(MatchResult):

    @property
    def success(self) -> Boolean:
        return Boolean(True)

    @property
    def message(self) -> List[str]:
        return List('success')


class FailureMatchResult(MatchResult):

    @property
    def success(self) -> Boolean:
        return Boolean(False)

    @property
    def message(self) -> List[str]:
        return List('failure')


class MatchResultAlg(MatchResult[List[A]], Generic[A]):

    def __init__(self, sub: List[MatchResult]) -> None:
        self.sub = sub

    @property
    def failures(self) -> List[MatchResult]:
        return self.sub.filter(_.failure)

    @property
    def message(self) -> List[str]:
        return (
            self.sub // _.message
            if self.success else
            self.failures // _.message
        )


class MatchResultAnd(MatchResultAlg):

    @property
    def success(self) -> Boolean:
        return self.sub.forall(_.success)


class MatchResultOr(MatchResultAlg):

    @property
    def success(self) -> Boolean:
        return self.sub.exists(_.success)


__all__ = ('MatchResult', 'SimpleMatchResult', 'MultiLineMatchResult',
           'NestedMatchResult', 'MultiMatchResult', 'ExistsMatchResult',
           'ForAllMatchResult', 'BadNestedMatch', 'SuccessMatchResult',
           'FailureMatchResult')
