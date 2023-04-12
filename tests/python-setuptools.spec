%global python3_pkgversion 3.11
Name:           python-setuptools
# on the CI we test different version of setuptools on different Fedora versions
# don't package software like this in Fedora please
%if 0%{?fedora} >= 37 || 0%{?rhel} >= 10
Version:        65.5.1
%else
Version:        59.6.0
%endif
Release:        0%{?dist}
Summary:        Easily build and distribute Python packages
# see the real Fedora package for explanation:
License:        MIT and (BSD or ASL 2.0)
URL:            https://pypi.python.org/pypi/setuptools
Source:         %{pypi_source setuptools %{version}}

# Patch from Fedora proper
%if 0%{?fedora} >= 37 || 0%{?rhel} >= 10
Patch:          https://src.fedoraproject.org/rpms/python-setuptools/raw/b61d86b9659/f/Remove-optional-or-unpackaged-test-deps.patch
%else
Patch:          https://src.fedoraproject.org/rpms/python-setuptools/raw/6fc093d6b3d/f/0001-Remove-optional-or-unpackaged-test-deps.patch
%endif

BuildArch:      noarch

BuildRequires:  python%{python3_pkgversion}-devel
BuildRequires:  python%{python3_pkgversion}-wheel
BuildRequires:  pyproject-rpm-macros
BuildRequires:  gcc

# too many missing tests deps in EPEL 9
%if 0%{?fedora}
%bcond_without tests
%else
%bcond_with tests
%endif

%description
This package tests 2 things:

 - %%{_pyproject_builddir} does not leak to pytest collection (rhzb#1935212)
 - TODO %%{pyproject_files} has escaped spaces (rhzb#1976363)


%package -n     python%{python3_pkgversion}-setuptools
Summary:        %{summary}

# For users who might see ModuleNotFoundError: No module named 'pkg_resoureces'
%py_provides    python%{python3_pkgversion}-pkg_resources
%py_provides    python%{python3_pkgversion}-pkg-resources

%description -n python%{python3_pkgversion}-setuptools
...


%prep
%autosetup -p1 -n setuptools-%{version}

%if 0%{?fedora} < 37 && 0%{?rhel} < 10
# The following test deps are optional and either not desired or not available in Fedora:
sed -Ei setup.cfg -e  '/\bpytest-(checkdocs|black|cov|mypy|enabler)\b/d' \
                  -e  '/\bflake8\b/d' \
                  -e  '/\bpaver\b/d'
# Strip pytest options from the above
sed -i pytest.ini -e 's/ --flake8//' \
                  -e 's/ --cov//'
%endif



%build
%pyproject_wheel


%install
%pyproject_install
%pyproject_save_files setuptools pkg_resources _distutils_hack

# https://github.com/pypa/setuptools/issues/2709
rm -rf %{buildroot}%{python3_sitelib}/pkg_resources/tests/
sed -i '/tests/d' %{pyproject_files}


%check
# https://github.com/pypa/setuptools/discussions/2607
rm pyproject.toml

%if %{with tests}
# We only run a subset of tests to speed things up and be less fragile
PRE_BUILT_SETUPTOOLS_WHEEL=%{_pyproject_wheeldir}/setuptools-%{version}-py3-none-any.whl \
PYTHONPATH=$(pwd) %pytest --ignore=pavement.py \
                          --ignore=setuptools/tests/test_develop.py \
                          --ignore=setuptools/tests/test_editable_install.py \
                          --ignore=setuptools/tests/config/test_apply_pyprojecttoml.py \
                          -k "sdist" -n %{_smp_build_ncpus}
%else
%pyproject_check_import
%endif

# Internal check that license file was recognized correctly
grep '^%%license' %{pyproject_files} > tested.license
echo '%%license %{python3_sitelib}/setuptools-%{version}.dist-info/LICENSE' > expected.license
diff tested.license expected.license


%files -n python%{python3_pkgversion}-setuptools -f %{pyproject_files}
%doc docs/* CHANGES.rst README.rst
%{python3_sitelib}/distutils-precedence.pth
