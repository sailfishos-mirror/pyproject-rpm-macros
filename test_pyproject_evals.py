"""Test RPM macro expansion from macros.pyproject.

This test was added late in the pyproject-rpm-macros life cycle and does
not include all macros.

When there is a regression that can be easily tested here, we'll add it.
"""

import os
import subprocess
from pathlib import Path

import pytest

BASEDIR = Path(__file__).parent

PRELOAD_LUA = (
    'package.preload["fedora.rpm.pyproject_getopt"]'
    f' = loadfile("{BASEDIR}/pyproject_getopt.lua")'
)


def rpm_eval(macro_call):
    """Expand an RPM macro using the local macros.pyproject and Lua files."""
    r = subprocess.run(
        [
            "rpm",
            f"--macros=/usr/lib/rpm/macros:/usr/lib/rpm/macros.d/macros.*:{BASEDIR}/macros.aaa-pyproject-srpm:{BASEDIR}/macros.pyproject",
            "--eval",
            f"%{{lua:{PRELOAD_LUA}}}{macro_call}",
        ],
        capture_output=True,
        text=True,
        env={**os.environ, "LANG": "C.UTF-8"},
    )
    assert r.returncode == 0, f"rpm --eval failed:\n{r.stderr}"
    return r.stdout.strip()


class TestPyprojectExtrasSubpkg:
    def test_short_options(self):
        r = rpm_eval("%pyproject_extras_subpkg -n test-pkg -f /dev/null myextra")
        assert "%package -n test-pkg+myextra" in r

    def test_long_name(self):
        r = rpm_eval("%pyproject_extras_subpkg --name test-pkg -f /dev/null myextra")
        assert "%package -n test-pkg+myextra" in r

    def test_multiple_extras(self):
        r = rpm_eval("%pyproject_extras_subpkg -n test-pkg -f /dev/null extra1 extra2")
        assert "%package -n test-pkg+extra1" in r
        assert "%package -n test-pkg+extra2" in r


class TestNormalizeName:
    @pytest.mark.parametrize(
        "input, expected",
        [
            ("Foo_Bar.baz", "foo-bar-baz"),
            ("UPPER", "upper"),
            ("already-normalized", "already-normalized"),
            ("dots...dashes---underscores___mixed", "dots-dashes-underscores-mixed"),
            ("simple", "simple"),
        ],
    )
    def test_normalize(self, input, expected):
        assert rpm_eval(f"%__pyproject_normalize_name {input}") == expected


@pytest.mark.parametrize(
    "macro",
    [
        "pyproject_files",
        "_pyproject_modules",
        "_pyproject_ghost_distinfo",
    ],
)
class TestPathMacros:
    def test_without_dist_name(self, macro):
        assert "pyproject-" in rpm_eval(f"%{macro}")

    def test_with_short_dist_name(self, macro):
        assert rpm_eval(f"%{macro} -D My_Package").endswith("-my-package")

    def test_with_long_dist_name(self, macro):
        assert rpm_eval(f"%{macro} --dist-name My_Package").endswith("-my-package")
