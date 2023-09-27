%global python3_pkgversion 38
Name:           python-django
Version:        3.0.7
Release:        0%{?dist}
Summary:        A high-level Python Web framework
License:        BSD
URL:            https://www.djangoproject.com/
Source0:        %{pypi_source Django}
BuildArch:      noarch

BuildRequires:  pyproject-rpm-macros
BuildRequires:  python%{python3_pkgversion}-devel
BuildRequires:  python%{python3_pkgversion}-setuptools
BuildRequires:  python%{python3_pkgversion}-wheel

%description
This package contains lang files.
Building this tests that lang files are marked with %%lang in filelist.


%package -n python%{python3_pkgversion}-django
Summary:        %{summary}

%description -n python%{python3_pkgversion}-django
...


%prep
%autosetup -p1 -n Django-%{version}
%py3_shebang_fix django/conf/project_template/manage.py-tpl django/bin/django-admin.py


%build
# remove .po files (in ideal world, we would rebuild the .mo files first)
find -name "*.po" | xargs rm -f

%pyproject_wheel


%install
%pyproject_install
%pyproject_save_files -l django


%check
# Internal check if generated lang entries are same as
# the ones generated using %%find_lang
%find_lang django
%find_lang djangojs

grep '^%%lang' %{pyproject_files} | sort > tested.lang
sort django.lang djangojs.lang > expected.lang
diff tested.lang expected.lang


%files -n python%{python3_pkgversion}-django -f %{pyproject_files}
%doc README.rst
%{_bindir}/django-admin
%{_bindir}/django-admin.py
