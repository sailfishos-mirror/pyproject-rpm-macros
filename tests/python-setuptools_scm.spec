%global python3_pkgversion 39
Name:           python-setuptools_scm
Version:        6.0.1

Release:        0%{?dist}
Summary:        The blessed package to manage your versions by SCM tags
License:        MIT
URL:            https://github.com/pypa/setuptools_scm/
Source0:        %{pypi_source setuptools_scm}

BuildArch:      noarch
BuildRequires:  python%{python3_pkgversion}-devel
BuildRequires:  python%{python3_pkgversion}-setuptools
BuildRequires:  python%{python3_pkgversion}-wheel
BuildRequires:  pyproject-rpm-macros
BuildRequires:  /usr/bin/git

# flake8 is still missing tests deps in EPEL 9
%if 0%{?fedora}
%bcond_without flake8
%else
%bcond_with flake8
%endif

%description
Here we test that %%pyproject_extras_subpkg works and generates
setuptools_scm[toml] extra subpackage.


%package -n python%{python3_pkgversion}-setuptools_scm
Summary:        %{summary}

%description -n python%{python3_pkgversion}-setuptools_scm
...

%pyproject_extras_subpkg -n python%{python3_pkgversion}-setuptools_scm toml


%prep
%autosetup -p1 -n setuptools_scm-%{version}


%build
%pyproject_wheel


%install
%pyproject_install
%pyproject_save_files -l setuptools_scm


%check
%if 0
# This tox should run all the toxenvs specified via -e in %%pyproject_buildrequires
# We only run some of the tests (running all of them requires network connection and is slow)
%tox -- -- -k test_version | tee toxlog

# Internal check for our macros: Assert both toxenvs were executed.
grep -E 'py%{python3_version_nodots}-test: (OK|commands succeeded)' toxlog
grep -E 'flake8: (OK|commands succeeded)' toxlog %{?!with_flake8:&& exit 1 || true}
%endif

# Internal check for our macros
# making sure that %%{_pyproject_ghost_distinfo} has the right content
test -f %{_pyproject_ghost_distinfo}
test "$(cat %{_pyproject_ghost_distinfo})" == "%ghost %{python3_sitelib}/setuptools_scm-%{version}.dist-info"


%files -n python%{python3_pkgversion}-setuptools_scm -f %{pyproject_files}
%doc README.rst
%doc CHANGELOG.rst
