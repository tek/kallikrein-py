from types import ModuleType
import pkgutil
from pkgutil import ModuleInfo  # type: ignore

from amino.regex import Regex, Match
from amino import Path, Either, List, _, Just, Empty, L, Left, __
from amino.util.numeric import parse_int
from amino.list import Lists

from kallikrein.run.data import (SpecLocation, LineSelector,
                                 FileMethodSelector, FileClassSelector,
                                 FileSelector, ModuleSelector)

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
    selector = FileSelector(path)
    return (
        (
            List.lines(path.read_text()) //
            cls_regex.match //
            __.group('name')
        )
        .traverse(
            L(SpecLocation.create)(mod, _, Empty(), selector, True), Either)
        if path.is_file() else
        Left('invalid path: {}'.format(loc))
    )


def lookup_file_lnum(path: Path, mod: str, lnum: int
                     ) -> Either[str, SpecLocation]:
    content = List.lines(path.read_text())[:lnum + 1].reversed
    selector = LineSelector(path, lnum)
    def found_def(name: str) -> Either[str, SpecLocation]:
        cls = content.find_map(cls_regex.match) // __.group('name')
        return cls // L(SpecLocation.create)(mod, _, Just(name), selector)
    def found_cls_def(match: Match) -> Either[str, SpecLocation]:
        name = match.group('name')
        return (
            name // found_def
            if match.group('kw').contains('def') else
            name // L(SpecLocation.create)(mod, _, Empty(), selector)
        )
    loc = content.find_map(cls_def_regex.match)
    return loc // found_cls_def


def lookup_file_select(fpath: Path, mod: str, select: str
                       ) -> Either[str, List[SpecLocation]]:
    parts = Lists.split(select, '.')
    meth = parts.lift(1)
    def create(cls: str) -> Either[str, SpecLocation]:
        selector = (
            meth /
            L(FileMethodSelector)(fpath, cls, _) |
            FileClassSelector(fpath, cls)
        )
        return SpecLocation.create(mod, cls, meth, selector)
    return (
        parts.head.to_either('empty select') //
        create /
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


def handle_file(match: Match, fpath: Path) -> Either[str, List[SpecLocation]]:
    mod = resolve_module(fpath)
    return (
        handle_file_select(match, mod, fpath)
        .o(lambda: handle_file_lnum(match, mod, fpath))
        .o(lambda: lookup_file(fpath))
        if fpath.is_file() else
        handle_dir(fpath)
        if fpath.is_dir() else
        Left('{} is not a file or dir'.format(fpath))
    )


def lookup_module(mod: ModuleType) -> List[SpecLocation]:
    names = List.wrap(mod.__all__)  # type: ignore
    selector = ModuleSelector(mod.__name__)
    return names // L(SpecLocation.create)(mod.__name__, _, Empty(), selector)


def exclude_module(mod: ModuleInfo) -> bool:
    return mod.ispkg or '._' in mod.name


def lookup_package(mod: ModuleType) -> List[SpecLocation]:
    name = mod.__name__
    path = mod.__path__  # type: ignore
    return (
        List.wrap(pkgutil.walk_packages(path, prefix='{}.'.format(name)))
        .filter_not(exclude_module) /
        _.name //
        Either.import_module //
        lookup_path
    )


def lookup_path(path: ModuleType) -> List[SpecLocation]:
    l = lookup_package if path.__package__ == path.__name__ else lookup_module
    return l(path)


def handle_path(path: str) -> Either[str, List[SpecLocation]]:
    return (
        (Either.import_module(path) / lookup_path)
        .o(lambda: SpecLocation.from_path(path) / List)
    )


def handle_dir(dpath: Path) -> Either[str, List[SpecLocation]]:
    return Either.import_module(resolve_module(dpath)) / lookup_path


def lookup_loc(loc: str) -> Either[str, List[SpecLocation]]:
    fpath = Path(loc)
    file_match = file_loc_regex.match(loc)
    path_match = path_loc_regex.match(loc)
    return (
        path_match // __.group('path') // handle_path
        if path_match.present else
        file_match.flat_apzip(lambda a: a.group('path') / Path)
        .flat_map2(handle_file)
        if file_match.present else
        handle_dir(fpath)
        if fpath.is_dir() else
        Left('invalid spec location: {}'.format(loc))
    )

__all__ = ('lookup_loc', 'lookup_file_lnum', 'lookup_file',
           'lookup_file_select')
