from types import ModuleType

from amino.regex import Regex, Match
from amino import Path, Either, List, _, Just, Empty, L, Left, __
from amino.util.numeric import parse_int
from amino.list import Lists

from kallikrein.run.data import SpecLocation

dir_loc_regex = None
file_loc_regex = Regex(
    r'(?P<path>.*?\.py)(:((?P<lnum>\d+)|(?P<select>\w+(\.\w+)?)))?$')
path_loc_regex = Regex(r'(?P<path>\w+(\.\w+)*)')
cls_def_regex = Regex(r'\s*(?P<kw>class|def) (?P<name>\w+)')
cls_regex = Regex(r'class (?P<name>\w+)')
init_name = '__init__.py'


def resolve_module(path: Path) -> str:
    def rec(p: Path) -> List[str]:
        return (
            rec(p.parent).cat(p.name)
            if List.wrap(p.iterdir()).exists(_.name == init_name) else
            List()
        )
    return rec(path.parent).cat(path.stem).mk_string('.')


def lookup_file(loc: str) -> Either[str, List[SpecLocation]]:
    path = Path(loc)
    mod = resolve_module(path)
    return (
        (
            List.lines(path.read_text()) //
            cls_regex.match //
            __.group('name')
        )
        .traverse(L(SpecLocation.create)(mod, _, Empty(), True), Either)
        if path.is_file() else
        Left('invalid path: {}'.format(loc))
    )


def lookup_file_lnum(path: Path, mod: str, lnum: int
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
            name // L(SpecLocation.create)(mod, _, Empty())
        )
    loc = content.find_map(cls_def_regex.match)
    return loc // found_cls_def


def lookup_file_select(fpath: Path, mod: str, select: str
                       ) -> Either[str, List[SpecLocation]]:
    parts = Lists.split(select, '.')
    meth = parts.lift(1)
    return (
        parts.head.to_either('empty select') //
        L(SpecLocation.create)(mod, _, meth) /
        List
    )


def handle_file_select(match: Match, mod: str, fpath: Path
                       ) -> Either[str, List[SpecLocation]]:
    return (match.group('select')) // L(lookup_file_select)(fpath, mod, _)


def handle_file_lnum(match: Match, mod: str, fpath: Path
                     ) -> Either[str, List[SpecLocation]]:
    return (
        match.group('lnum') //
        parse_int /
        (_ - 1) //
        L(lookup_file_lnum)(fpath, mod, _) /
        List
    )


def handle_dir(match: Match, dpath: Path) -> Either[str, List[SpecLocation]]:
    return Left('dir not implemented yet')


def handle_file(match: Match, fpath: Path) -> Either[str, List[SpecLocation]]:
    mod = resolve_module(fpath)
    return (
        handle_file_select(match, mod, fpath)
        .o(lambda: handle_file_lnum(match, mod, fpath))
        .o(lambda: lookup_file(fpath))
        if fpath.is_file() else
        handle_dir(match, fpath)
        if fpath.is_dir() else
        Left('{} is not a file or dir'.format(fpath))
    )


def lookup_path_classes(mod: ModuleType) -> List[SpecLocation]:
    names = List.wrap(mod.__all__)
    return names.traverse(
        L(SpecLocation.create)(mod.__name__, _, Empty()), Either)


def handle_path(match: Match, path: str) -> Either[str, List[SpecLocation]]:
    return (
        (Either.import_module(path) // lookup_path_classes)
        .o(lambda: SpecLocation.from_path(path) / List)
    )


def lookup_loc(loc: str) -> Either[str, List[SpecLocation]]:
    file_match = file_loc_regex.match(loc)
    path_match = path_loc_regex.match(loc)
    return (
        path_match.flat_apzip(__.group('path'))
        .flat_map2(handle_path)
        if path_match.present else
        file_match.flat_apzip(lambda a: a.group('path') / Path)
        .flat_map2(handle_file)
        if file_match.present else
        Left('invalid spec location: {}'.format(loc))
    )

__all__ = ('lookup_loc', 'lookup_by_path', 'lookup_file_lnum',
           'lookup_file')
