Name:           double-install
Version:        0
Release:        0%{?dist}
Summary:        Install 2 wheels
License:        BSD-3-Clause AND MIT
%global         markupsafe_version 2.0.1
%global         tldr_version 0.4.4
Source1:        https://github.com/pallets/markupsafe/archive/%{markupsafe_version}/MarkupSafe-%{markupsafe_version}.tar.gz
Source2:        %{pypi_source tldr %{tldr_version}}

BuildRequires:  gcc
BuildRequires:  python3-devel

%description
This package tests that we can build and install 2 wheels at once.
One of them is "noarch" and one has an extension module.
This also tests the -d option for %%pyproject_buildrequires/%%pyproject_wheel
and the -D option for %%pyproject_save_files/%%pyproject_check_import.


%package -n python3-double-markupsafe
Summary:        MarkupSafe from double-install test

%description -n python3-double-markupsafe
MarkupSafe subpackage.


%package -n python3-double-tldr
Summary:        tldr from double-install test
BuildArch:      noarch

%description -n python3-double-tldr
tldr subpackage.


%prep
%setup -Tc
tar xf %{SOURCE1}
tar xf %{SOURCE2}


%generate_buildrequires
%pyproject_buildrequires --no-runtime --directory markupsafe-%{markupsafe_version}
%pyproject_buildrequires --directory tldr-%{tldr_version}


%build
%pyproject_wheel --directory markupsafe-%{markupsafe_version}
%pyproject_wheel --directory tldr-%{tldr_version}


%install
set -o pipefail
(
# This should install both the wheels:
%pyproject_install
) 2>&1 | tee install.log
%pyproject_save_files --dist-name markupsafe markupsafe
%pyproject_save_files -D tldr tldr +auto


%check
# Internal check for the value of %%{pyproject_build_lib}
cd markupsafe-%{markupsafe_version}
%if 0%{?rhel} == 9
test "%{pyproject_build_lib}" == "%{_builddir}/%{buildsubdir}/markupsafe-%{markupsafe_version}/build/lib.%{python3_platform}-%{python3_version}"
%else
test "%{pyproject_build_lib}" == "%{_builddir}/%{buildsubdir}/markupsafe-%{markupsafe_version}/build/lib.%{python3_platform}-cpython-%{python3_version_nodots}"
%endif
cd ../tldr-%{tldr_version}
test "%{pyproject_build_lib}" == "%{_builddir}/%{buildsubdir}/tldr-%{tldr_version}/build/lib"
cd ..
# Internal regression check for %%pyproject_install with multiple wheels
grep 'binary operator expected' install.log && exit 1 || true
grep 'too many arguments' install.log && exit 1 || true
# Check that %%pyproject_check_import -D works
%pyproject_check_import -D markupsafe
%pyproject_check_import -D tldr


%files -n python3-double-markupsafe -f %{pyproject_files -D markupsafe}

%files -n python3-double-tldr -f %{pyproject_files --dist-name tldr}
