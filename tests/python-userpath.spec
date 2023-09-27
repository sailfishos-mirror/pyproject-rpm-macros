%global python3_pkgversion 3.11
Name:           python-userpath
Version:        1.8.0
Release:        1%{?dist}
Summary:        Cross-platform tool for adding locations to the user PATH
License:        MIT
URL:            https://github.com/ofek/userpath
Source:         %{pypi_source userpath}
BuildArch:      noarch
BuildRequires:  pyproject-rpm-macros
BuildRequires:  python%{python3_pkgversion}-devel

%description
This package uses hatchling as build backend.
This package is tested because:

 - the licenses are stored in a dist-info subdirectory
   https://bugzilla.redhat.com/1985340
   (as of hatchling 0.22.0, not yet marked as License-File)


%package -n     python%{python3_pkgversion}-userpath
Summary:        %{summary}

%description -n python%{python3_pkgversion}-userpath
...


%prep
%autosetup -p1 -n userpath-%{version}
sed -Ei '/^(coverage)$/d' requirements-dev.txt


%build
%pyproject_wheel


%install
%pyproject_install
%pyproject_save_files -l userpath


%check
%pytest

%if 0%{?fedora} || 0%{?rhel} > 9
# Internal check that license file was recognized correctly with hatchling 1.9.0+
grep '^%%license' %{pyproject_files} > tested.license
echo '%%license %{python3_sitelib}/userpath-%{version}.dist-info/licenses/LICENSE.txt' > expected.license
diff tested.license expected.license
%endif


%files -n python%{python3_pkgversion}-userpath -f %{pyproject_files}
%{_bindir}/userpath
