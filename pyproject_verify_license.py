"""
Minimal, stdlib-only SPDX license-expression comparator.

Compares two SPDX license expressions for semantic equivalence.
AND/OR are treated as commutative, associative and idempotent;
"A WITH B" is atomic. It does not resolve SPDX synonyms
(GPL-2.0+ != GPL-2.0-or-later), validate identifiers,
or perform boolean absorption.

Expressions are parsed straight into order-independent canonical keys (nested
tuples); two expressions are equivalent if their keys compare equal.
"""

import argparse
import re
import sys

try:
    # tomllib is in the standard library since 3.11.0b1
    import tomllib
except ImportError:
    import tomli as tomllib


class LicenseExpressionError(ValueError):
    """Raised when a license expression string cannot be parsed."""


class LicenseVerificationError(Exception):
    """A reportable reason the license check failed."""


class LicenseExpression:
    """An SPDX license expression parsed into an order-independent canonical key.

    The input string is parsed on construction into a nested-tuple ``key``; two
    expressions are equivalent iff their keys compare equal, so instances can be
    compared directly:

    >>> LicenseExpression("MIT OR Apache-2.0") == LicenseExpression("Apache-2.0 OR MIT")
    True
    >>> LicenseExpression("GPL-2.0+") == LicenseExpression("GPL-2.0-or-later")
    False

    AND/OR are treated as commutative, associative and idempotent; "A WITH B" is
    atomic. Synonyms are not resolved and identifiers are not validated.

    Raise LicenseExpressionError on syntactically invalid or empty input.

    The grammar (SPDX operator precedence: `WITH` > `AND` > `OR`):

        or_expr   := and_expr ( "OR"  and_expr )*
        and_expr  := with_expr ( "AND" with_expr )*
        with_expr := primary ( "WITH" EXCEPTION_ID )?   # left side must be a bare license id
        primary   := "(" or_expr ")" | LICENSE_ID
    """

    _KEYWORDS = {"AND", "OR", "WITH"}
    _TOKEN_RE = re.compile(r"\s*(\(|\)|[^\s()]+)")

    def __init__(self, expression):
        if expression is None:
            raise LicenseExpressionError("Expression is None")
        self.expression = expression
        self.tokens = self._TOKEN_RE.findall(expression)
        if not self.tokens:
            raise LicenseExpressionError("Empty license expression")
        self.pos = 0
        self.key = self._parse_or()
        if self._peek() is not None:
            raise LicenseExpressionError(f"Unexpected token: {self._peek()}")

    def __eq__(self, other):
        if not isinstance(other, LicenseExpression):
            return NotImplemented
        return self.key == other.key

    def __hash__(self):
        return hash(self.key)

    def __repr__(self):
        return f"{type(self).__name__}({self.expression!r})"

    def _peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def _advance(self):
        tok = self._peek()
        self.pos += 1
        return tok

    def _accept(self, keyword):
        tok = self._peek()
        if tok not in (None, "(", ")") and tok.upper() == keyword:
            self.pos += 1
            return True
        return False

    def _parse_or(self):
        operands = [self._parse_and()]
        while self._accept("OR"):
            operands.append(self._parse_and())
        return operands[0] if len(operands) == 1 else self._junction("or", operands)

    def _parse_and(self):
        operands = [self._parse_with()]
        while self._accept("AND"):
            operands.append(self._parse_with())
        return operands[0] if len(operands) == 1 else self._junction("and", operands)

    def _parse_with(self):
        parenthesized = self._peek() == "("
        node = self._parse_primary()
        if self._accept("WITH"):
            if parenthesized or not (isinstance(node, tuple) and node[0] == "license"):
                raise LicenseExpressionError("WITH must follow a single license id")
            exc = self._advance()
            if exc in (None, "(", ")") or exc.upper() in self._KEYWORDS:
                raise LicenseExpressionError("Expected an exception id after WITH")
            node = ("with", node, exc.lower())
        return node

    def _parse_primary(self):
        tok = self._advance()
        if tok is None:
            raise LicenseExpressionError("Unexpected end of expression")
        if tok == "(":
            node = self._parse_or()
            if self._advance() != ")":
                raise LicenseExpressionError("Missing closing parenthesis")
            return node
        if tok == ")":
            raise LicenseExpressionError("Unexpected ')'")
        if tok.upper() in self._KEYWORDS:
            raise LicenseExpressionError(f"Unexpected operator: {tok}")
        return ("license", tok.lower())

    @staticmethod
    def _junction(operator, operands):
        """Combine operands under AND/OR: flatten same-operator nesting,
        deduplicate, and collapse singletons -- yielding a
        commutative/associative/idempotent key."""
        keys = set()
        for op in operands:
            if isinstance(op, tuple) and op[0] == operator:
                keys.update(op[1])
            else:
                keys.add(op)
        if len(keys) == 1:
            return next(iter(keys))
        return (operator, tuple(sorted(keys)))


def read_project_license(pyproject_path):
    """Return the static SPDX string from [project].license, or raise."""
    try:
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
    except FileNotFoundError:
        raise LicenseVerificationError(
            f"{pyproject_path} not found; cannot verify the license."
        )
    except tomllib.TOMLDecodeError as e:
        raise LicenseVerificationError(
            f"{pyproject_path} is not valid TOML: {e}"
        )

    project = data.get("project", {})
    # We don't expect the metadata to be malformed like that,
    # but being defensive just to be sure
    if not isinstance(project, dict):
        raise LicenseVerificationError(
            "project is not a table, it cannot be processed."
        )
    dynamic = project.get("dynamic", [])
    if not isinstance(dynamic, list):
        raise LicenseVerificationError(
            "project.dynamic is not a list, it cannot be processed."
        )
    if "license" in dynamic:
        raise LicenseVerificationError(
            "project.license is declared dynamic, so it cannot be verified."
        )
    if "license" not in project:
        raise LicenseVerificationError(
            "project.license is not set in pyproject.toml."
        )
    license_value = project["license"]
    if not isinstance(license_value, str):
        raise LicenseVerificationError(
            "project.license is not a string SPDX expression (found "
            f"{type(license_value).__name__}). The deprecated table form "
            "({text=…}/{file=…}) is not supported."
        )
    return license_value


def verify(spec_license, pyproject_path="pyproject.toml"):
    upstream = read_project_license(pyproject_path)
    try:
        match = LicenseExpression(spec_license) == LicenseExpression(upstream)
    except LicenseExpressionError as e:
        raise LicenseVerificationError(
            f"Cannot parse a license expression: {e}"
        )
    if not match:
        raise LicenseVerificationError(
            f"Spec License tag {spec_license} does not match upstream "
            f"project.license {upstream}."
        )


def argparser():
    parser = argparse.ArgumentParser(prog='%pyproject_verify_license')
    parser.add_argument('spec_license')
    return parser


def main(argv=None):
    args = argparser().parse_args(argv)
    try:
        verify(args.spec_license)
    except LicenseVerificationError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
