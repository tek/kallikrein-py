from amino.test import Spec
from amino import List, L
from amino.anon import lambda_str

from kallikrein import k
from kallikrein.matchers import throw, contain
from kallikrein.matchers.throw import Throw
from kallikrein.matchers.contain import Contain
from kallikrein.expectation import Expectation


class Error1(Exception):
    pass


class Error2(Exception):
    pass


class Error3(Exception):

    def __init__(self, *items: str) -> None:
        Exception.__init__(self)
        self.items = items

    def __contains__(self, item: str) -> bool:
        return item in self.items

    def __str__(self) -> str:
        return 'Error3({})'.format(self.items)


def _throw1() -> None:
    raise Error1()


def _throw2() -> None:
    raise Error2()


def _nothrow() -> None:
    pass


def _throw3(exc: Exception) -> None:
    raise exc


class ThrowSpec(Spec):

    def _run(self, exp: Expectation, success: bool):
        result = exp.evaluate.attempt
        assert result.present
        assert result.value.success == success
        return result.value

    def simple_success(self) -> None:
        result = self._run(k(_throw1).must(throw(Error1)), True)
        assert result.report == Throw.simple_success.format(
            _throw1.__name__, '`{}`'.format(Error1.__name__))

    def simple_failure_nothing(self) -> None:
        result = self._run(k(_nothrow).must(throw(Error1)), False)
        assert result.report == Throw.simple_failure.format(
            _nothrow.__name__, Throw.no_exception, Error1.__name__)

    def simple_failure_different(self) -> None:
        result = self._run(k(_throw2).must(throw(Error1)), False)
        assert result.report == Throw.simple_failure.format(
            _throw2.__name__, '`{}`'.format(Error2.__name__), Error1.__name__)

    def nested_success(self) -> None:
        data = List.random_string()
        exc = Error3(data)
        f = L(_throw3)(exc)
        result = self._run(k(f).must(throw(contain(data))), True)
        line1 = Throw.nested_success.format(lambda_str(f))
        line2 = ' {}'.format(Contain.success.format(exc, data))
        assert result.report_lines == List(line1, line2)

    def nested_failure_nothing(self) -> None:
        result = self._run(k(_nothrow).must(throw(contain(1))), False)
        assert result.report == Throw.nested_failure_not_raise.format(
            _nothrow.__name__)

    def nested_failure_different(self) -> None:
        data = List.random_string()
        invalid = 'invalid'
        exc = Error3(data)
        f = L(_throw3)(exc)
        result = self._run(k(f).must(throw(contain(invalid))), False)
        line1 = Throw.nested_failure.format(lambda_str(f))
        line2 = ' {}'.format(Contain.failure.format(exc, invalid))
        assert result.report_lines == List(line1, line2)

__all__ = ('ThrowSpec',)
