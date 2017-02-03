from kallikrein.expectation import Expectation, FatalSpecResult
from kallikrein.util.string import red, red_cross


head = 'spec with exception'
l1 = 'failure'
error = 'too many puppies'


def raiser() -> None:
    raise Exception(error)


class Exc:
    __doc__ = '''{}
    {} $failure
    '''.format(head, l1)

    def failure(self) -> Expectation:
        raiser()

target_report_exception = '''{}
 {} {}
  {}
     File "{}", line 20, in failure
       raiser()
     File "{}", line 11, in raiser
       raise Exception(error)
   {}
'''.format(head, red_cross, l1, FatalSpecResult.error_head, __file__, __file__,
           red('Exception: {}'.format(error)))

__all__ = ('Exc',)
