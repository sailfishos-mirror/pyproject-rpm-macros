import pytest

from pyproject_verify_license import LicenseVerificationError, LicenseExpressionError
from pyproject_verify_license import argparser, main, verify, LicenseExpression


EQUIVALENT = [
    ("MIT OR Apache-2.0", "Apache-2.0 OR MIT"),  # commutativity
    ("(MIT AND BSD-3-Clause) AND ISC", "MIT AND (BSD-3-Clause AND ISC)"),  # associativity
    ("MIT AND MIT", "MIT"),  # idempotence
    ("mit or apache-2.0", "MIT OR Apache-2.0"),  # case-fold
    ("(MIT OR BSD-3-Clause) AND MIT", "MIT AND (BSD-3-Clause OR MIT)"),  # nested mixed
    ("Apache-2.0 WITH LLVM-exception", "apache-2.0 WITH llvm-exception"),  # WITH atomic
    ("(MIT AND BSD-3-Clause) OR ISC", "MIT AND BSD-3-Clause OR ISC"),
    ("(MIT WITH X)", "MIT WITH X"),
]

NOT_EQUIVALENT = [
    ("MIT", "BSD-3-Clause"),  # different licenses
    ("Apache-2.0 WITH LLVM-exception", "Apache-2.0"),  # WITH vs bare
    ("GPL-2.0", "GPL-2.0+"),  # bare vs or-later
    ("GPL-2.0+", "GPL-2.0-or-later"),  # no deprecated-spelling synonym resolution
    ("LGPL-2.1", "LGPL-2.1-only"),  # no deprecated-spelling synonym resolution
    ("bzip2-1.0.5", "bzip2-1.0.6"),  # no synonym resolution
    ("(MIT OR BSD-3-Clause) AND MIT", "MIT"),  # no boolean absorption
]

INVALID = [
    "MIT AND",  # dangling operator
    "(MIT OR BSD-3-Clause",  # missing parenthesis
    "(MIT OR BSD-3-Clause) WITH LLVM-exception",  # bad WITH left-hand side
    "",  # empty
    "   ",  # whitespace only
    "MIT OR OR Apache-2.0",  # unexpected operator
    "(MIT WITH X) WITH Y",
    "(MIT) WITH X",
]


@pytest.mark.parametrize("expr1, expr2", EQUIVALENT)
def test_equivalent(expr1, expr2):
    assert (LicenseExpression(expr1) == LicenseExpression(expr2))


@pytest.mark.parametrize("expr1, expr2", NOT_EQUIVALENT)
def test_not_equivalent(expr1, expr2):
    assert not (LicenseExpression(expr1) == LicenseExpression(expr2))


@pytest.mark.parametrize("expression", INVALID)
def test_invalid(expression):
    with pytest.raises(LicenseExpressionError):
        LicenseExpression(expression)


def test_none_is_invalid():
    with pytest.raises(LicenseExpressionError):
        LicenseExpression(None)


def write_pyproject(tmp_path, content):
    path = tmp_path / "pyproject.toml"
    path.write_text(content)
    return path


def test_missing_pyproject_toml(tmp_path):
    with pytest.raises(LicenseVerificationError, match="not found"):
        verify("MIT", tmp_path / "pyproject.toml")


def test_invalid_toml(tmp_path):
    path = write_pyproject(tmp_path, "this is not [ valid toml")
    with pytest.raises(LicenseVerificationError, match="not valid TOML"):
        verify("MIT", path)


def test_missing_license_key(tmp_path):
    path = write_pyproject(tmp_path, """
        [project]
        name = "spam"
        version = "1.0"
    """)
    with pytest.raises(LicenseVerificationError, match="not set in pyproject.toml"):
        verify("MIT", path)


def test_dynamic_license(tmp_path):
    path = write_pyproject(tmp_path, """
        [project]
        name = "spam"
        version = "1.0"
        dynamic = ["license"]
    """)
    with pytest.raises(LicenseVerificationError, match="declared dynamic"):
        verify("MIT", path)


def test_non_string_license(tmp_path):
    path = write_pyproject(tmp_path, """
        [project]
        name = "spam"
        version = "1.0"
        license = {text = "MIT"}
    """)
    with pytest.raises(LicenseVerificationError, match="not a string SPDX expression"):
        verify("MIT", path)


def test_unparseable_license(tmp_path):
    path = write_pyproject(tmp_path, """
        [project]
        name = "spam"
        version = "1.0"
        license = "MIT AND"
    """)
    with pytest.raises(LicenseVerificationError, match="Cannot parse a license expression"):
        verify("MIT", path)


def test_unparseable_spec_license(tmp_path):
    path = write_pyproject(tmp_path, """
        [project]
        name = "spam"
        version = "1.0"
        license = "MIT"
    """)
    with pytest.raises(LicenseVerificationError, match="Cannot parse a license expression"):
        verify("MIT AND", path)


def test_mismatch(tmp_path):
    path = write_pyproject(tmp_path, """
        [project]
        name = "spam"
        version = "1.0"
        license = "Apache-2.0"
    """)
    with pytest.raises(LicenseVerificationError, match="does not match upstream"):
        verify("MIT", path)


def test_success(tmp_path):
    path = write_pyproject(tmp_path, """
        [project]
        name = "spam"
        version = "1.0"
        license = "MIT AND BSD-3-Clause"
    """)
    verify("BSD-3-Clause and MIT", path)


def test_gnu_family_deprecated_spelling_not_resolved(tmp_path):
    # GPL-2.0+ and GPL-2.0-or-later are the same license, but this module does
    # not resolve deprecated-spelling synonyms, so they are treated as a mismatch.
    path = write_pyproject(tmp_path, """
        [project]
        name = "spam"
        version = "1.0"
        license = "GPL-2.0-or-later"
    """)
    with pytest.raises(LicenseVerificationError, match="does not match upstream"):
        verify("GPL-2.0+", path)


def test_cli_positional_argument_required():
    with pytest.raises(SystemExit):
        argparser().parse_args([])


def test_cli_success(tmp_path, monkeypatch):
    write_pyproject(tmp_path, """
        [project]
        name = "spam"
        version = "1.0"
        license = "MIT"
    """)
    monkeypatch.chdir(tmp_path)
    assert main(["MIT"]) == 0


def test_cli_failure(tmp_path, monkeypatch, capsys):
    write_pyproject(tmp_path, """
        [project]
        name = "spam"
        version = "1.0"
        license = "Apache-2.0"
    """)
    monkeypatch.chdir(tmp_path)
    assert main(["MIT"]) == 1
    assert "does not match upstream" in capsys.readouterr().err
