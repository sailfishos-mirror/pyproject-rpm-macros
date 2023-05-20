Name:           config-settings-test
Version:        1.0.0
Release:        1%{?dist}
Summary:        Test config_settings support

License:        MIT
URL:            ...
Source0:        config_settings_test_backend.py


%description
%{summary}.


%prep
%autosetup -cT

cp -p %{sources} .

cat <<'EOF' >config_settings.py
"""
This is a test package
"""
EOF

cat <<'EOF' >pyproject.toml
[build-system]
build-backend = "config_settings_test_backend"
backend-path = ["."]
requires = ["flit-core"]

[project]
name = "config_settings"
version = "%{version}"
dynamic = ["description"]
EOF


%generate_buildrequires
%pyproject_buildrequires -C abc=123 -C xyz=456 -C--option-with-dashes=1
%pyproject_buildrequires -C abc=123 -C xyz=456 -C--option-with-dashes=1 -w


%build
%pyproject_wheel -C abc=123 -C xyz=456 -C--option-with-dashes=1


%changelog
* Fri May 19 2023 Maxwell G <maxwell@gtmx.me>
- Initial package
