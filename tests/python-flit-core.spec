%global python3_pkgversion 3.11
Name:           python-flit-core
Version:        3.0.0
Release:        0%{?dist}
Summary:        Distribution-building parts of Flit

License:        BSD
URL:            https://pypi.org/project/flit-core/
Source0:        https://github.com/takluyver/flit/archive/%{version}/flit-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python%{python3_pkgversion}-devel
BuildRequires:  pyproject-rpm-macros

%description
Test a wheel built from a subdirectory.
Test a build with pyproject.toml backend-path = .
flit-core builds with flit-core.


%package -n python%{python3_pkgversion}-flit-core
Summary:        %{summary}

%description -n python%{python3_pkgversion}-flit-core
...


%prep
%autosetup -p1 -n flit-%{version}


%build
cd flit_core
%pyproject_wheel
cd ..


%install
%pyproject_install
# there is no license file marked as License-File, hence not using -l
%pyproject_save_files flit_core


%check
# internal check for our macros, we assume there is no license
grep -F %%license %{pyproject_files} && exit 1 || true


%files -n python%{python3_pkgversion}-flit-core -f %{pyproject_files}
