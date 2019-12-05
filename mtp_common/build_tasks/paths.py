import collections
import contextlib
import datetime
import os
import pathlib
import shlex


@contextlib.contextmanager
def in_dir(path):
    old_path = os.getcwd()
    try:
        os.chdir(path)
        yield path
    finally:
        os.chdir(old_path)


def paths_for_shell(paths, separator=' '):
    """
    Converts a list of paths for use in shell commands
    """
    paths = filter(None, paths)
    paths = map(lambda path: shlex.quote(str(path)), paths)
    if separator is None:
        return paths
    return separator.join(paths)


class FileSet(collections.Iterable, collections.Sized):
    def __init__(self, *include, root='.'):
        self.include = list(map(str, include))
        if isinstance(root, str):
            root = pathlib.Path(root)
        self.root = root

    def __repr__(self):
        paths = ' '.join(self.include)
        return f'<File set: {paths}>'

    def include(self, pattern):
        self.include.append(str(pattern))
        return self

    def __iter__(self):
        paths = []
        for pattern in self.include:
            paths.extend(self.root.glob(pattern))
        return iter(set(paths))

    def __bool__(self):
        for _ in self:
            return True
        return False

    def __len__(self):
        return len(list(self))

    def exists(self):
        return bool(self)

    def files(self):
        return filter(lambda path: path.is_file(), self)

    @property
    def latest_modification(self):
        try:
            return datetime.datetime.fromtimestamp(max(path.stat().st_mtime for path in self.files()))
        except ValueError:
            return None

    def modified_since(self, other_file_set):
        this = self.latest_modification
        other = other_file_set.latest_modification
        return this and (not other or this > other)
