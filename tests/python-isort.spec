%global python3_pkgversion 38
%global modname isort

Name:               python-%{modname}
Version:            4.3.21
Release:            7%{?dist}
Summary:            Python utility / library to sort Python imports

License:            MIT
URL:                https://github.com/timothycrosley/%{modname}
Source0:            %{url}/archive/%{version}-2/%{modname}-%{version}-2.tar.gz
BuildArch:          noarch
BuildRequires:      python%{python3_pkgversion}-devel
BuildRequires:      python%{python3_pkgversion}-setuptools
BuildRequires:      python%{python3_pkgversion}-wheel
BuildRequires:      pyproject-rpm-macros

%description
This package contains executables.
Building this tests that executables are not listed when +auto is not used
with %%pyproject_save_files.

This package also uses %%{python3_pkgversion} in name and has a very limited
set of dependencies -- allows to set a different value for it repeatedly.

%package -n python%{python3_pkgversion}-%{modname}
Summary:            %{summary}

%description -n python%{python3_pkgversion}-%{modname}
%{summary}.

%if 0%{?rhel} == 9
%global python3_pkgversion 3.11
%package -n python%{python3_pkgversion}-%{modname}
Summary:            %{summary}

%description -n python%{python3_pkgversion}-%{modname}
%{summary}.

%global python3_pkgversion 38
%endif


%prep
%autosetup -n %{modname}-%{version}-2


%build
%pyproject_wheel
%if 0%{?rhel} == 8
%global python3_pkgversion 3.11
%pyproject_wheel
%endif


%install
%if 0%{?rhel} == 8
%global python3_pkgversion 3.11
%pyproject_install
%pyproject_save_files -l isort
%global python3_pkgversion 38
%endif
# we keep this one last so /usr/bin/isort is installed with python38 shebang
%pyproject_install
%pyproject_save_files isort


%check
# Internal check if the instalation outputs expected result
test -d %{buildroot}%{python3_sitelib}/%{modname}/
test -d %{buildroot}%{python3_sitelib}/%{modname}-%{version}.dist-info/

# Internal check that executables are not present when +auto was not used with %%pyproject_save_files
grep -F %{_bindir}/%{modname} %{pyproject_files} && exit 1 || true

%if 0%{?rhel} == 8
# Internal check that correct versions are in correct %%{pyproject_files}s
diff %{pyproject_files} <(grep -F python3.8/site-packages %{pyproject_files})

%global python3_pkgversion 3.11
test -d %{buildroot}%{_usr}/lib/python3.11/site-packages/%{modname}/
test -d %{buildroot}%{_usr}/lib/python3.11/site-packages/%{modname}-%{version}.dist-info/
diff %{pyproject_files} <(grep -F python3.11/site-packages %{pyproject_files})
%global python3_pkgversion 38
%endif


%files -n python%{python3_pkgversion}-%{modname} -f %{pyproject_files}
%license LICENSE
%doc README.rst *.md
%{_bindir}/%{modname}
%if 0%{?rhel} == 8
%global python3_pkgversion 3.11
%files -n python%{python3_pkgversion}-%{modname} -f %{pyproject_files}
%doc README.rst *.md
%global python3_pkgversion 38
%endif
