from amino.regex import Regex, Match
from amino import Path, Either, List, _, Just, Empty, L, Left, __

from ribosome.request.base import parse_int

from kallikrein.run.data import SpecLocation

file_loc_regex = Regex(
    r'(?P<path>.*?)(\.(?P<cls>\w+(\.(?P<meth>\w+))?)|:(?P<lnum>\d+))?$')
cls_def_regex = Regex(r'\s*(?P<kw>class|def) (?P<name>\w+)')
cls_regex = Regex(r'\s*class (?P<name>\w+)')
init_name = '__init__.py'


def resolve_module(path: Path) -> List[str]:
    return (
        resolve_module(path.parent).cat(path.name)
        if List.wrap(path.iterdir()).exists(_.name == init_name) else
        List()
    )


def lookup_by_line(path: Path, mod: str, lnum: int
                   ) -> Either[str, SpecLocation]:
    content = List.lines(path.read_text())[:lnum + 1].reversed
    def found_def(name: str) -> Either[str, SpecLocation]:
        cls = content.find_map(cls_regex.match) // __.group('name')
        return cls // L(SpecLocation.create)(mod, _, Just(name))
    def found_cls_def(match: Match) -> Either[str, SpecLocation]:
        name = match.group('name')
        return (
            name // found_def
            if match.group('kw').contains('def') else
            name / L(SpecLocation.create)(mod, _, Empty())
        )
    loc = content.find_map(cls_def_regex.match)
    return loc // found_cls_def


def lookup_by_path(match: Match, path: str) -> Either[str, SpecLocation]:
    p = Path(path)
    mod = resolve_module(p.parent).cat(p.stem).mk_string('.')
    return (
        (match.group('lnum') // parse_int // L(lookup_by_line)(p, mod, _))
        .o(match.group('cls') //
            L(SpecLocation.create)(mod, _, match.group('meth')))
        if p.is_file() else
        Left('invalid path: {}'.format(path))
    )


def lookup_loc(loc: str) -> Either[str, SpecLocation]:
    def handle(match: Match) -> Either[str, SpecLocation]:
        return match.group('path') // L(lookup_by_path)(match, _)
    return file_loc_regex.match(loc) // handle

__all__ = ('lookup_loc', 'lookup_by_path', 'lookup_by_line')
