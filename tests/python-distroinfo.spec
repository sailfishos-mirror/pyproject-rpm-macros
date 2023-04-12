%global python3_pkgversion 3.11
Name:             python-distroinfo
Version:          0.3.2
Release:          0%{?dist}
Summary:          Parsing and querying distribution metadata stored in text/YAML files
License:          ASL 2.0
URL:              https://github.com/softwarefactory-project/distroinfo
Source0:          %{pypi_source distroinfo}
BuildArch:        noarch

BuildRequires:    pyproject-rpm-macros
BuildRequires:    python%{python3_pkgversion}-devel
BuildRequires:    python%{python3_pkgversion}-pytest
BuildRequires:    python%{python3_pkgversion}-setuptools
BuildRequires:    git-core

%description
This package uses setuptools and pbr.
Run %%pyproject_check_import with top-level modules filtering.


%package -n python%{python3_pkgversion}-distroinfo
Summary:          %{summary}

%description -n python%{python3_pkgversion}-distroinfo
...


%prep
%autosetup -p1 -n distroinfo-%{version}
# we don't need pytest-runner
sed -Ei "s/(, )?'pytest-runner'//" setup.py


%build
%pyproject_wheel


%install
%pyproject_install
%pyproject_save_files distroinfo


%check
%pytest
%pyproject_check_import -t


%files -n python%{python3_pkgversion}-distroinfo -f %{pyproject_files}
%doc README.rst AUTHORS
%license LICENSE
