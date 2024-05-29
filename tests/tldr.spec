%global python3_pkgversion 38
Name:           tldr
Version:        0.4.4
Release:        1%{?dist}
Summary:        Simplified and community-driven man pages

License:        MIT
URL:            https://github.com/tldr-pages/tldr-python-client
Source0:        %{pypi_source}

BuildArch:      noarch
BuildRequires:  python%{python3_pkgversion}-devel
BuildRequires:  python%{python3_pkgversion}-setuptools_scm
BuildRequires:  python%{python3_pkgversion}-wheel
BuildRequires:  pyproject-rpm-macros

%description
A Python package containing executables.
Building this tests:
- there are no bytecompiled files in %%{_bindir}
- the executable's shebang is adjusted properly
- file direct_url.json isn't created
- installation to custom prefix works

%prep
%autosetup -n %{name}-%{version}

%build
%pyproject_wheel

%install
%pyproject_install
%pyproject_save_files tldr +auto

%check
# Internal check for our macros: tests we don't ship __pycache__ in bindir
test ! -d %{buildroot}%{_bindir}/__pycache__

# Internal check for our macros: tests we have a proper shebang line
head -n1 %{buildroot}%{_bindir}/%{name}.py | grep -E '#!\s*%{python3}\s+%{py3_shbang_opts}\s*$'

# Internal check for our macros: tests that direct_url.json file wasn't created
test ! -e %{buildroot}%{python3_sitelib}/*.dist-info/direct_url.json

# Internal check for the value of %%{pyproject_build_lib} in a noarch package
%if 0%{?rhel} <= 9
test "%{pyproject_build_lib}" == "$(echo %{_pyproject_builddir}/pip-req-build-*/build/lib)"
%else
test "%{pyproject_build_lib}" == "${PWD}/build/lib"
%endif

%if 0%{?rhel} != 8 && 0%{?rhel} != 9
# Internal check for custom prefix
grep '^/usr' %{pyproject_files} && exit 1 || true
grep '^/app' %{pyproject_files}
%endif

%files -f %pyproject_files
%license LICENSE
%doc README.md
