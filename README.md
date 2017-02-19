## Intro
_kallikrein_ is a test framework inspired by [specs2], focused on functional
purity and composability.

## Install
```
pip install kallikrein
```

## Write
Spec classes need only define a docstring containing interpolation expressions
that specify which of the class' methods are specs:

```python
from kallikrein import k
from kallikrein.matchers import contain, greater_equal, forall
from amino import List

class ASpec:
    '''example specifications

    this test is simple
    simple spec $simple

    these tests are nested
    successful nesting $nested
    failed spec $failure '''

    def setup(self):
        self.a = 3

    def simple(self):
        return k(3).must(greater_equal(self.a))

    def nested(self):
        return k(List(1, 2, 3)).must(contain(greater_equal(self.a)))

    def failure(self):
        return k(List('abc', 'abc', 'ac')).must(forall(contain('b')))
```

There is no magic involved, the names in the docstring are simply used with
`getattr`.

The expectations aren't evaluated in-place, but after having been returned to
the spec runner. There is an alternative, impure version called `unsafe_k` that
raises an exception.

Logical operations on expectations are possible:
```python
k(3).must(equal(3)) & k(4).must(greater_equal(2)) | k(List(2)).must(contain(2))
```
associativity via parentheses is not yet implemented.

THe same applies for matchers:
```python
k(3).must(equal(3) & greater_equal(2))
```

If a spec class has `setup` and `teardown` methods, they are called once before
and after each individual spec.

The decorator `kallikrein.pending` can be used to mark a spec as pending:
```python
@pending
def not_implemented_yet(self):
  pass
```

## Run
```
% klk mod.path.to.ASpec
```
The output looks like this:

![output](img/output.jpg)

Selection of specs works as well by specifying a file name.
Optionally, a line number or method name can be appended to run a single case:

```
% klk mod/path/to.py:18
% klk mod.path.to.ASpec.simple
```

Modules, packages, directories and files are valid as well, in which case a
recursive search is done returning all valid specs specified in the modules'
`__all__` attribute:

```
% klk mod.path
% klk mod/path/to
```

## Extend
`must` expects a `Match` instance for its argument which is produced by a
`Matcher` when called with a target value and produces a `MatchResult` when
evaluated.
Subclassing `Matcher` and implementing the `match` and `match_nested` methods
is a simple way to create a custom matcher, but there is a much more flexible
concept available.

The `TCMatcher` class uses [amino]'s typeclass system to allow special
treatment of any type by any matcher without having to reimplement the
matchers.
A typeclass matcher consists of two string templates for assembling the success
and failure messages and two instances of the typeclasses `Predicate` and
`Nesting`.

Defining classes for those typeclasses for a specific type automatically
registers them as handlers for that type in the desired matcher.

This is the implementation of `contain` for reference:

```python
from collections.abc import Container, Iterable


class PredContain(Predicate):
    pass


class NestContain(Nesting):
    pass


is_container = L(issubclass)(_, Container)
is_collection = L(issubclass)(_, Iterable)


class PredContainCollection(PredContain, pred=is_container):

    def check(self, exp: Collection[A], target: A) -> Boolean:
        return Boolean(target in exp)


class NestContainCollection(NestContain, pred=is_collection):

    def match(self, exp: Collection[A], target: Match) -> List[MatchResult[B]]:
        return List.wrap([target.evaluate(e) for e in exp])

    def wrap(self, name: str, exp: Collection[A], nested: List[MatchResult[B]]
             ) -> MatchResult[A]:
        return ExistsMatchResult(name, exp, nested)


success = '`{}` contains `{}`'
failure = '`{}` does not contain `{}`'
contain = matcher('contain', success, failure, PredContain, NestContain)


class PredContainMaybe(PredContain, tpe=Maybe):

    def check(self, exp: Maybe[A], target: A) -> Boolean:
        return Boolean(exp.contains(target))
```
The `PredContain` and `NestContain` classes are used to link instances for
specific types to the contain matcher.
The matcher checks all available instances for eligibility for the type of the
checked expectable and calls the `check`, `match` and `wrap` methods on the
respective instances.

In this example, the instances use a predicate function to check whether a type
can be handled by them, in this case, if they are virtual subclasses of
`Container` or `Iterable`.
The simple way would be to pass `tpe=list` to the metaclass constructor instead
of `pred=is_container`, but that would not allow any other iterable type to be
matched.
The instance `PredContainMaybe` demonstrates the use of the `tpe` variant and
shows that additional instances for arbitrary types can be added without having
to change the internal logic of **kallikrein**.

The internal part of `TCMatcher` constructs a `SimpleMatchResult` from the
result of `Predicate.check`, indicating success of the match, and the two
strings supplied to the constructor that describe the success and failure.

Because nested matches must be handled specifically to the matcher,
the `MatchResult` must be constructed in the implementation.
`ExistsMatchResult` is one possible variant; it receives the list of nested
match results (one for each list element) and creates a detailed error
message, succeeding if at least one nested `MatchResult` is successful.

[specs2]: https://github.com/etorreborre/specs2
[amino]: https://github.com/tek/amino
