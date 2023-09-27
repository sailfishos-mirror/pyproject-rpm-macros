%global python3_pkgversion 38
%global pypi_name entrypoints
Name:           python-%{pypi_name}
Version:        0.3
Release:        0%{?dist}
Summary:        Discover and load entry points from installed packages
License:        MIT
URL:            https://entrypoints.readthedocs.io/
Source0:        %{pypi_source}
BuildArch:      noarch

BuildRequires:  pyproject-rpm-macros
BuildRequires:  python%{python3_pkgversion}-devel

%description
This package contains one .py module
Building this tests the flit build backend.


%package -n python%{python3_pkgversion}-%{pypi_name}
Summary:        %{summary}

%description -n python%{python3_pkgversion}-%{pypi_name}
%{summary}.


%prep
%autosetup -p1 -n %{pypi_name}-%{version}


%build
%pyproject_wheel


%install
%pyproject_install
# the license is not marked as License-File, hence -L
%pyproject_save_files entrypoints -L


%check
# Internal check: Top level __pycache__ is never owned
grep -E '/__pycache__$' %{pyproject_files} && exit 1 || true
grep -E '/__pycache__/$' %{pyproject_files} && exit 1 || true
grep -F '/__pycache__/' %{pyproject_files}


%files -n python%{python3_pkgversion}-%{pypi_name} -f %{pyproject_files}
%doc README.rst
%license LICENSE
