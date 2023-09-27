%global python3_pkgversion 3.11
Name:           python-poetry-core
Version:        1.0.0
Release:        0%{?dist}
Summary:        Poetry PEP 517 Build Backend

License:        MIT
URL:            https://pypi.org/project/poetry-core/
Source0:        %{pypi_source poetry-core}

BuildArch:      noarch
BuildRequires:  python%{python3_pkgversion}-devel
BuildRequires:  pyproject-rpm-macros

%description
Test a build with pyproject.toml backend-path = [.]
poetry-core builds with poetry-core.


%package -n python%{python3_pkgversion}-poetry-core
Summary:        %{summary}

%description -n python%{python3_pkgversion}-poetry-core
...


%prep
%autosetup -p1 -n poetry-core-%{version}


%build
%pyproject_wheel


%install
%pyproject_install
# the license is not marked as License-File by poetry-core, hence -L
%pyproject_save_files -L poetry

# internal check for our macros, -l must fail:
%pyproject_save_files -l poetry && exit 1 || true

%files -n python%{python3_pkgversion}-poetry-core -f %{pyproject_files}
%doc README.md
%license LICENSE
