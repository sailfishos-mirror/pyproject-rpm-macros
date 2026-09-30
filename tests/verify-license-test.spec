Name:           verify-license-test
Version:        0
Release:        0%{?dist}

Summary:        ...
# A fake license declaration for testing purposes
License:        MIT AND BSD-3-Clause

BuildRequires:  python3-devel
BuildRequires:  pyproject-rpm-macros
BuildRequires:  (python3dist(tomli) if python3-devel < 3.11)


%description
Fake spec file to test %%pyproject_verify_license


%prep
cat > pyproject.toml <<EOF
[project]
name = "verify-license-test"
version = "0"
license = "MIT AND BSD-3-Clause"
EOF

# %%pyproject_verify_license only needs pyproject.toml, so it must work in %%prep
%pyproject_verify_license

mkdir equivalent
# same license, written in a different (but semantically equivalent) way
cat > equivalent/pyproject.toml <<EOF
[project]
name = "verify-license-test"
version = "0"
license = "bsd-3-clause and mit"
EOF

mkdir mismatch
cat > mismatch/pyproject.toml <<EOF
[project]
name = "verify-license-test"
version = "0"
license = "Apache-2.0"
EOF

mkdir dynamic
cat > dynamic/pyproject.toml <<EOF
[project]
name = "verify-license-test"
version = "0"
dynamic = ["license"]
EOF

mkdir no-license
cat > no-license/pyproject.toml <<EOF
[project]
name = "verify-license-test"
version = "0"
EOF

mkdir table-license
cat > table-license/pyproject.toml <<EOF
[project]
name = "verify-license-test"
version = "0"
license = {text = "MIT AND BSD-3-Clause"}
EOF

mkdir bad-expression
cat > bad-expression/pyproject.toml <<EOF
[project]
name = "verify-license-test"
version = "0"
license = "MIT AND"
EOF

mkdir broken
cat > broken/pyproject.toml <<EOF
this is not valid [ toml
EOF

# an existing directory with no pyproject.toml at all
mkdir no-pyproject


%generate_buildrequires
%pyproject_buildrequires --no-use-build-system


%check
# Assert a failing macro aborts the build by running it in a fresh `sh -e`.
# A subshell or `if`/`&&` condition would disable `set -e`, letting the macro's
# trailing popd mask the failure.
assert_check_fails() {
    if sh -e; then
        echo "ERROR: expected %%pyproject_verify_license to fail the build" >&2
        exit 1
    fi
}

# matching license succeeds
%pyproject_verify_license

# case/order-insensitive equivalent expression succeeds
%pyproject_verify_license --directory equivalent

# --directory must restore the original CWD afterwards (pushd/popd are paired)
_before_dir=$(pwd -P)
%pyproject_verify_license --directory equivalent
test "$(pwd -P)" = "$_before_dir"

# mismatched license fails the build
assert_check_fails <<'EOF'
%{pyproject_verify_license --directory mismatch}
EOF

# an explicit positional argument overrides the spec License: tag and is compared instead
%pyproject_verify_license --directory mismatch Apache-2.0

# ... and still fails the build when it doesn't match
assert_check_fails <<'EOF'
%{pyproject_verify_license --directory equivalent Apache-2.0}
EOF

# dynamic license fails the build
assert_check_fails <<'EOF'
%{pyproject_verify_license --directory dynamic}
EOF

# missing license key fails the build
assert_check_fails <<'EOF'
%{pyproject_verify_license --directory no-license}
EOF

# non-string (deprecated table form) license fails the build
assert_check_fails <<'EOF'
%{pyproject_verify_license --directory table-license}
EOF

# unparseable license expression fails the build
assert_check_fails <<'EOF'
%{pyproject_verify_license --directory bad-expression}
EOF

# unparseable license expression given as argument fails the build
assert_check_fails <<'EOF'
%{pyproject_verify_license --directory equivalent bsd-3-clause and}
EOF

# invalid TOML fails the build
assert_check_fails <<'EOF'
%{pyproject_verify_license --directory broken}
EOF

# missing pyproject.toml fails the build
assert_check_fails <<'EOF'
%{pyproject_verify_license --directory no-pyproject}
EOF
