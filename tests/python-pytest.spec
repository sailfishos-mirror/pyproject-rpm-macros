%global python3_pkgversion 3.11
%global pypi_name pytest
Name:           python-%{pypi_name}
Version:        6.2.5
Release:        0%{?dist}
Summary:        Simple powerful testing with Python
License:        MIT
URL:            https://pytest.org
Source0:        %{pypi_source}

BuildArch:      noarch
BuildRequires:  python%{python3_pkgversion}-devel
BuildRequires:  python%{python3_pkgversion}-setuptools
BuildRequires:  python%{python3_pkgversion}-setuptools_scm
BuildRequires:  python%{python3_pkgversion}-wheel
BuildRequires:  python%{python3_pkgversion}-attrs
BuildRequires:  pyproject-rpm-macros

# no xmlschema packaged for EPEL 9 yet, cannot run tests on EPEL
%if 0%{?fedora}
%bcond_without tests
%else
%bcond_with tests
%endif

%description
This is a pure Python package with executables. It has a test suite in tox.ini
and test dependencies specified via the [test] extra.
Building this tests:
- generating runtime and test dependencies by both tox.ini and extras
- pyproject.toml with the setuptools backend and setuptools-scm
- passing arguments into %%tox

%package -n python%{python3_pkgversion}-%{pypi_name}
Summary:        %{summary}

%description -n python%{python3_pkgversion}-%{pypi_name}
%{summary}.


%prep
%autosetup -p1 -n %{pypi_name}-%{version}
# remove optional test dependencies we don't like to pull in
sed -E -i '/mock|nose/d' setup.cfg
# internal check for our macros: insert a subprocess echo to setup.py
# to ensure it's not generated as BuildRequires
echo 'import os; os.system("echo if-this-is-generated-the-build-will-fail")' >> setup.py


%build
%pyproject_wheel


%install
%pyproject_install
%pyproject_save_files -l '*pytest' +auto


%check
%if %{with tests}
# Only run one test (which uses a test-only dependency, hypothesis)
# See how to pass options trough the macro to tox, trough tox to pytest
%tox -- -- -k metafunc
%else
%pyproject_check_import
%endif


%files -n python%{python3_pkgversion}-%{pypi_name} -f %{pyproject_files}
%doc README.rst
%doc CHANGELOG.rst
