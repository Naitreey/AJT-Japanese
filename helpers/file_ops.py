# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import functools
import os
import subprocess
from collections.abc import Iterable

from anki.utils import no_bundled_libs

try:
    from ..ajt_common.utils import find_executable
except ImportError:
    from ajt_common.utils import find_executable

THIS_ADDON_MODULE = __name__.split(".")[0]


def walk_parents(current_dir: str) -> Iterable[str]:
    while not os.path.samefile(parent_dir := os.path.dirname(current_dir), current_dir):
        yield parent_dir
        current_dir = parent_dir


def resolve_relative_path(*paths) -> str:
    """Return path to file inside the add-on's dir."""
    for parent_dir in walk_parents(__file__):
        if os.path.basename(parent_dir) == THIS_ADDON_MODULE:
            return os.path.join(parent_dir, *paths)


def touch(path):
    with open(path, "a"):
        os.utime(path, None)


def find_config_json() -> str:
    """Used when testing/debugging."""
    for parent_dir in walk_parents(__file__):
        if os.path.isfile(path := os.path.join(parent_dir, "config.json")):
            return path


@functools.cache
def user_files_dir() -> str:
    """Return path to the user files directory."""
    for parent_dir in walk_parents(__file__):
        if os.path.isdir(dir_path := os.path.join(parent_dir, "user_files")):
            return dir_path


def open_file(path: str) -> None:
    """
    Select file in lf, the preferred terminal file manager, or open it with xdg-open.
    """
    from aqt.qt import QDesktopServices, QUrl

    if (terminal := os.getenv("TERMINAL")) and (lf := (os.getenv("FILE") or find_executable("lf"))):
        subprocess.Popen(
            [terminal, "-e", lf, path],
            shell=False,
            start_new_session=True,
        )
    elif opener := find_executable("xdg-open"):
        subprocess.Popen(
            [opener, f"file://{path}"],
            shell=False,
            start_new_session=True,
        )
    else:
        with no_bundled_libs():
            QDesktopServices.openUrl(QUrl(f"file://{path}"))


def main():
    print("config", find_config_json())
    print("user files", user_files_dir())
    print("open file", open_file("/etc/hosts"))


if __name__ == "__main__":
    main()
