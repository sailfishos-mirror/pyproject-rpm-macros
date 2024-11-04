pyproject RPM macros
====================

These macros allow projects that follow the Python [packaging specifications]
to be packaged as RPMs.

They work for:

* traditional Setuptools-based projects that use the `setup.py` file,
* newer Setuptools-based projects that have a `setup.cfg` file,
* general Python projects that use the [PEP 517] `pyproject.toml` file (which allows using any build system, such as setuptools, flit or poetry).

These macros replace `%py3_build` and `%py3_install`, which only work with `setup.py`.

[packaging specifications]: https://packaging.python.org/specifications/


Usage
-----

To use these macros, first BuildRequire the devel package for the Python you
are building against. In Fedora, that's `python3-devel`.

    BuildRequires: python3-devel

The macros will be pulled in as a dependency on Fedora and EPEL 9+.  
In other distributions you need to BuildRequire the macros as well:

    BuildRequires: python3-devel
    BuildRequires: pyproject-rpm-macros

Next, you need to generate more build dependencies (of your projects and
the macros themselves) by running `%pyproject_buildrequires` in the
`%generate_buildrequires` section:

    %generate_buildrequires
    %pyproject_buildrequires

This will add build dependencies according to [PEP 517] and [PEP 518].
This also adds run-time dependencies by default and
can add test-time dependencies, see the section below.
If you need more dependencies, such as non-Python libraries, BuildRequire
them manually.

Note that `%generate_buildrequires` may produce error messages `(exit 11)` in
the build log. This is expected behavior of BuildRequires generators; see
[the Fedora change] for details.

[the Fedora change]: https://fedoraproject.org/wiki/Changes/DynamicBuildRequires

Then, build a wheel in `%build` with `%pyproject_wheel`:

    %build
    %pyproject_wheel

And install the wheel in `%install` with `%pyproject_install`:

    %install
    %pyproject_install

`%pyproject_install` installs all wheels in `pyproject-wheeldir/` located in the root of the source tree.


Adding run-time and test-time dependencies
------------------------------------------

To run tests or import checks in the `%check` section,
the package's runtime dependencies need to also be included as build requirements.

Hence, `%pyproject_buildrequires` also generates runtime dependencies by default.

For this to work, the project's build system must support the [prepare-metadata-for-build-wheel hook].
The popular buildsystems (setuptools, flit, poetry) do support it.

This behavior can be disabled
(e.g. when the project's build system does not support it)
using the `-R` flag:

    %generate_buildrequires
    %pyproject_buildrequires -R

Alternatively, if the project specifies its dependencies in the pyproject.toml
`[project]` table (as defined in [PEP 621](https://www.python.org/dev/peps/pep-0621/)),
the runtime dependencies can be obtained by reading that metadata.

This can be enabled by using the `-p` flag.
This flag supports reading both the runtime dependencies, and the selected extras
(see the `-x` flag described below).

Please note that not all build backends which use pyproject.toml support the
`[project]` table scheme.
For example, poetry-core (at least in 1.9.0) defines package metadata in the
custom `[tool.poetry]` table which is not supported by the `%pyproject_buildrequires` macro.

Finally, the runtime dependencies can be obtained by building the wheel and reading the metadata from the built wheel.
This can be enabled with the `-w` flag and cannot be combined with `-p`.
Support for building wheels with `%pyproject_buildrequires -w` is **provisional** and the behavior might change.
Please subscribe to Fedora's [python-devel list] if you use the option.

    %generate_buildrequires
    %pyproject_buildrequires -w

When this is used, the wheel is going to be built at least twice,
becasue the `%generate_buildrequires` section runs repeatedly.
To avoid accidentally reusing a wheel leaking from a previous (different) build,
it cannot be reused between `%generate_buildrequires` rounds.
Contrarily to that, rebuilding the wheel again in the `%build` section is redundant
and the packager can omit the `%build` section entirely
to reuse the wheel built from the last round of `%generate_buildrequires`.
Be extra careful when attempting to modify the sources after `%pyproject_buildrequires`,
e.g. when running extra commands in the `%build` section:

    %build
    cython src/wrong.pyx  # this is too late with %%pyproject_buildrequires -w
    %pyproject_wheel

For projects that specify test requirements using an [`extra`
provide](https://packaging.python.org/specifications/core-metadata/#provides-extra-multiple-use),
these can be added using the `-x` flag.
Multiple extras can be supplied by repeating the flag or as a comma separated list.
For example, if upstream suggests installing test dependencies with
`pip install mypackage[testing]`, the test deps would be generated by:

    %generate_buildrequires
    %pyproject_buildrequires -x testing

For projects that specify test requirements in their [tox] configuration,
these can be added using the `-t` flag (default tox environment)
or the `-e` flag followed by the tox environment.
The default tox environment (such as `py37` assuming the Fedora's Python version is 3.7)
is available in the `%{toxenv}` macro.
For example, if upstream suggests running the tests on Python 3.7 with `tox -e py37`,
the test deps would be generated by:

    %generate_buildrequires
    %pyproject_buildrequires -t

If upstream uses a custom derived environment, such as `py37-unit`, use:

    %pyproject_buildrequires -e %{toxenv}-unit

Or specify more environments if needed:

    %pyproject_buildrequires -e %{toxenv}-unit,%{toxenv}-integration

The `-e` option redefines `%{toxenv}` for further reuse.
Use `%{default_toxenv}` to get the default value.

The `-t`/`-e` option uses [tox-current-env]'s `--print-deps-to-file` behind the scenes.

If your package specifies some tox plugins in `tox.requires`,
such plugins will be BuildRequired as well.
Not all plugins are guaranteed to play well with [tox-current-env],
in worst case, patch/sed the requirement out from the tox configuration.

Note that neither `-x` or `-t` can be used with `-R`,
because runtime dependencies are always required for testing.
You can only use those options if the build backend  supports the [prepare-metadata-for-build-wheel hook],
or together with `-p` or `-w`.

[tox]: https://tox.readthedocs.io/
[tox-current-env]: https://github.com/fedora-python/tox-current-env/
[prepare-metadata-for-build-wheel hook]: https://www.python.org/dev/peps/pep-0517/#prepare-metadata-for-build-wheel
[python-devel list]: https://lists.fedoraproject.org/archives/list/python-devel@lists.fedoraproject.org/

Additionally to generated requirements you can supply multiple file names to `%pyproject_buildrequires` macro.
Dependencies will be loaded from them:

    %pyproject_buildrequires requirements/tests.in requirements/docs.in requirements/dev.in

For packages not using build system you can use `-N` to entirely skip automatical
generation of requirements and install requirements only from manually specified files.
`-N` option implies `-R` and cannot be used in combination with other options mentioned above
(`-w`, `-e`, `-t`, `-x`, `-p`).

The `%pyproject_buildrequires` macro also accepts the `-r` flag for backward compatibility;
it means "include runtime dependencies" which has been the default since version 0-53.


Passing config settings to build backends
-----------------------------------------

The `%pyproject_buildrequires` and `%pyproject_wheel` macros accept a `-C` flag
to pass [configuration settings][config_settings] to the build backend.
Options take the form of `-C KEY`, `-C KEY=VALUE`, or `-C--option-with-dashes`.
Pass `-C` multiple times to specify multiple options.
This option is equivalent to pip's `--config-settings` flag.
These are passed on to PEP 517 hooks' `config_settings` argument as a Python
dictionary.

The `%pyproject_buildrequires` macro passes these options to the
`get_requires_for_build_wheel` and `prepare_metadata_for_build_wheel` hooks.
Passing `-C` to `%pyproject_buildrequires` is incompatible with `-N` which does
not call these hooks at all.

The `%pyproject_wheel` macro passes these options to the `build_wheel` hook.

Consult the project's upstream documentation and/or the corresponding build
backend's documentation for more information.
Note that some projects don't use config settings at all
and other projects may only accept config settings for one of the two steps.

Note that the current implementation of the macros uses `pip` to build wheels.
On some systems (notably on RHEL 9 with Python 3.9),
`pip` is too old to understand `--config-settings`.
Using the `-C` option for `%pyproject_wheel` (or `%pyproject_buildrequires -w`)
is not supported there and will result to an error like:

    Usage:   
      /usr/bin/python3 -m pip wheel [options] <requirement specifier> ...
      ...
    no such option: --config-settings

[config_settings]: https://peps.python.org/pep-0517/#config-settings


Running tox based tests
-----------------------

In case you want to run the tests as specified in [tox] configuration,
you must use `%pyproject_buildrequires` with `-t` or `-e` as explained above.
Then, use the `%tox` macro in `%check`:

    %check
    %tox

The macro:

 - Sets environment variables via `%{py3_test_envvars}`, namely:
     - Always prepends `$PATH` with `%{buildroot}%{_bindir}`
     - If not defined, sets `$PYTHONPATH` to `%{buildroot}%{python3_sitearch}:%{buildroot}%{python3_sitelib}`
 - If not defined, sets `$TOX_TESTENV_PASSENV` to `*`
 - Runs `tox` with `-q` (quiet), `--recreate` and `--current-env` (from [tox-current-env]) flags
 - Implicitly uses the tox environment name stored in `%{toxenv}` - as overridden by `%pyproject_buildrequires -e`

By using the `-e` flag, you can use a different tox environment(s):

    %check
    %tox
    %if %{with integration_test}
    %tox -e %{default_toxenv}-integration
    %endif

If you wish to provide custom `tox` flags or arguments, add them after `--`:

    %tox -- --flag-for-tox

If you wish to pass custom `posargs` to tox, use another `--`:

    %tox -- --flag-for-tox -- --flag-for-posargs

Or (note the two sequential `--`s):

    %tox -- -- --flag-for-posargs



Generating the %files section
-----------------------------

To generate the list of files in the `%files` section, you can use `%pyproject_save_files` after the `%pyproject_install` macro.
It takes toplevel module names (i.e. the names used with `import` in Python) and stores paths for those modules and metadata for the package (dist-info directory) to a file stored at `%{pyproject_files}`.
For example, if a package provides the modules `requests` and `_requests`, write:

    %install
    %pyproject_install
    %pyproject_save_files requests _requests

To add listed files to the `%files` section, use `%files -f %{pyproject_files}`.
Note that you still need to add any documentation manually (for now).

    %files -n python3-requests -f %{pyproject_files}
    %doc README.rst

You can use globs in the module names if listing them explicitly would be too tedious:

    %install
    %pyproject_install
    %pyproject_save_files '*requests'

In fully automated environments, you can use the `*` glob to include all modules (put it in single quotes to prevent Shell from expanding it). In Fedora however, you should always use a more specific glob to avoid accidentally packaging unwanted files (for example, a top level module named `test`).

Speaking about automated environments, some files cannot be classified with `%pyproject_save_files`, but it is possible to list all unclassified files by adding a special `+auto` argument.

    %install
    %pyproject_install
    %pyproject_save_files '*' +auto
    
    %files -n python3-requests -f %{pyproject_files}

However, in Fedora packages, always list executables explicitly to avoid unintended collisions with other packages or accidental missing executables:

    %install
    %pyproject_install
    %pyproject_save_files requests _requests
    
    %files -n python3-requests -f %{pyproject_files}
    %doc README.rst
    %{_bindir}/downloader

`%pyproject_save_files` can automatically mark license files with `%license` macro
and  language (`*.mo`) files with `%lang` macro and appropriate language code.
Only license files declared via [PEP 639] `License-File` field are detected.
[PEP 639] is still provisional and can be changed in the future.
It is possible to use the `-l` flag to declare that a missing license should
terminate the build or `-L` (the default) to explicitly disable this check.
Packagers are encouraged to use the `-l` flag when the `%license` file is not manually listed in `%files`
to avoid accidentally losing the file in a future version.
When the `%license` file is manually listed in `%files`,
packagers can use the `-L` flag to ensure future compatibility in case the `-l` behavior eventually becomes a default.

Note that `%pyproject_save_files` uses data from the [RECORD file](https://www.python.org/dev/peps/pep-0627/).
If you wish to rename, remove or otherwise change the installed files of a package
*after* `%pyproject_install`, `%pyproject_save_files` might break.
If possible, remove/rename such files in `%prep`.
If not possible, avoid using `%pyproject_save_files` or edit/replace `%{pyproject_files}`.


Performing an import check on all importable modules
----------------------------------------------------

If the upstream test suite cannot be used during the package build
and you use `%pyproject_save_files`,
you can benefit from the `%pyproject_check_import` macro.
If `%pyproject_save_files` is not used, calling `%pyproject_check_import` will fail.

When `%pyproject_save_files` is invoked,
it creates a list of all valid and public (i.e. not starting with `_`)
importable module names found in the package.
Each top-level module name matches at least one of the globs provided as an argument to `%pyproject_save_files`.
This list is then usable by `%pyproject_check_import` which performs an import check for each listed module.
When a module fails to import, the build fails.

The modules are imported from both installed and buildroot's `%{python3_sitearch}`
and `%{python3_sitelib}`, not from the current directory.

Use the macro in `%check`:

    %check
    %pyproject_check_import

By using the `-e` flag, you can exclude module names matching the given glob(s) from the import check
(put it in single quotes to prevent Shell from expanding it).
The flag can be used repeatedly.
For example, to exclude all submodules ending with `config` and all submodules starting with `test`, you can use:

    %pyproject_check_import -e '*.config' -e '*.test*'

There must be at least one module left for the import check;
if, as a result of greedy excluding, no modules are left to check, the check fails.

When the `-t` flag is used, only top-level modules are checked,
qualified module names with a dot (`.`) are excluded.
If the modules detected by `%pyproject_save_files` are `requests`, `requests.models`, and `requests.packages`, this will only perform an import of `requests`:

    %pyproject_check_import -t

The modifying flags should only be used when there is a valid reason for not checking all available modules.
The reason should be documented in a comment.

The `%pyproject_check_import` macro also accepts positional arguments with
additional qualified module names to check, useful for example if some modules are installed manually.
Note that filtering by `-t`/`-e` also applies to the positional arguments.

Another macro, `%_pyproject_check_import_allow_no_modules` allows to pass the import check,
even if no Python modules are detected in the package.
This may be a valid case for packages containing e.g. typing stubs.
Don't use this macro in Fedora packages.
It's only intended to be used in automated build environments such as Copr.


Generating Extras subpackages
-----------------------------

The `%pyproject_extras_subpkg` macro generates simple subpackage(s)
for Python extras.

The macro should be placed after the base package's `%description` to avoid
issues in building the SRPM.

For example, if the `requests` project's metadata defines the extras
`security` and `socks`, the following invocation will generate the subpackage
`python3-requests+security` that provides `python3dist(requests[security])`,
and a similar one for `socks`.

    %pyproject_extras_subpkg -n python3-requests security socks

The macro works like `%python_extras_subpkg`,
except the `-i`/`-f`/`-F` arguments are optional and discouraged.
A filelist written by `%pyproject_install` is used by default.
For more information on `%python_extras_subpkg`, see the [Fedora change].

[Fedora change]: https://fedoraproject.org/wiki/Changes/PythonExtras

These arguments are still required:

* -n: name of the “base” package (e.g. python3-requests)
* Positional arguments: the extra name(s).
  Multiple subpackages are generated when multiple names are provided.


Provisional: Declarative Buildsystem (RPM 4.20+)
------------------------------------------------

It is possible to reduce some of the spec boilerplate by using the provided
pyproject [declarative buildsystem].
This option is only available with RPM 4.20+ (e.g. in Fedora 41+).
The declarative buildsystem is **provisional** and the behavior might change.
Please subscribe to Fedora's [python-devel list] if you use the feature.

To enable the pyproject declarative buildsystem, use the following:

    BuildSystem:          pyproject
    BuildOption(install): <options for %%pyproject_save_files>

That way, RPM will automatically fill-in the `%prep`, `%generate_buildrequires`,
`%build`, `%install`, and `%check` sections the following defaults:

    %prep
    %autosetup -p1 -C
    
    %generate_buildrequires
    %pyproject_buildrequires
    
    %build
    %pyproject_wheel
    
    %install
    %pyproject_install
    %pyproject_save_files <options from BuildOption(install)>
    
    %check
    %pyproject_check_import

To pass options to the individual macros, use `BuildOption` (see the [documentation of declarative buildsystems][declarative buildsystem]).

    # pass options for %%pyproject_save_files (mandatory when not overriding %%install)
    BuildOption(install): -l _module +auto

    # replace the default options for %%autosetup
    BuildOption(prep): -S git_am -C

    # pass options to %%pyproject_buildrequires
    BuildOption(generate_buildrequires): docs-requirements.txt -t

    # pass options to %%pyproject_wheel
    BuildOption(build): -C--global-option=--no-cython-compile

    # pass options to %%pyproject_check_import
    BuildOption(check): -e '*.test*'

Alternatively, you can supply your own sections to override the automatic ones:

    BuildOption(generate_buildrequires): -w
    ...
    %build
    # do nothing, the wheel was built in %%generate_buildrequires

You can append to end of the automatic sections:

    %check -a
    # run %%pytest after %%pyproject_check_import
    %pytest

Or prepend to the beginning of them:

    %prep -p
    # run %%gpgverify before %%autosetup
    %gpgverify -k2 -s1 -d0

[declarative buildsystem]: https://rpm-software-management.github.io/rpm/manual/buildsystem.html


Limitations
-----------

`%pyproject_install` changes shebang lines of every Python script in `%{buildroot}%{_bindir}` to `#!%{__python3} %{py3_shbang_opt}` (`#!/usr/bin/python3 -s`).
Existing Python flags in shebangs are preserved.
For example `#!/usr/bin/python3 -Ru` will be updated to `#!/usr/bin/python3 -sRu`.
Sometimes, this can interfere with tests that run such scripts directly by name,
because in tests we usually rely on `PYTHONPATH` (and `-s` ignores that).
Would this behavior be undesired for any reason,
undefine `%{py3_shbang_opt}` to turn it off.

Some valid Python version specifiers are not supported.

When a dependency is specified via an URL or local path, for example as:

    https://github.com/ActiveState/appdirs/archive/8eacfa312d77aba28d483fbfb6f6fc54099622be.zip
    /some/path/foo-1.2.3.tar.gz
    git+https://github.com/sphinx-doc/sphinx.git@96dbe5e3

The `%pyproject_buildrequires` macro is unable to convert it to an appropriate RPM requirement and will fail.
If the URL contains the `packageName @` prefix as specified in [PEP 508],
the requirement will be generated without a version constraint:

    appdirs@https://github.com/ActiveState/appdirs/archive/8eacfa312d77aba28d483fbfb6f6fc54099622be.zip
    foo@file:///some/path/foo-1.2.3.tar.gz

Will be converted to:

    python3dist(appdirs)
    python3dist(foo)

Alternatively, when an URL requirement parsed from a text file
given as positional argument to `%pyproject_buildrequires`
contains the `#egg=packageName` fragment,
as documented in [pip's documentation]:

    git+https://github.com/sphinx-doc/sphinx.git@96dbe5e3#egg=sphinx

The requirements will be converted to package names without versions, e.g.:

    python3dist(sphinx)

However upstreams usually only use direct URLs for their requirements as workarounds,
so be prepared for problems.

[PEP 508]: https://www.python.org/dev/peps/pep-0508/
[PEP 517]: https://www.python.org/dev/peps/pep-0517/
[PEP 518]: https://www.python.org/dev/peps/pep-0518/
[PEP 639]: https://www.python.org/dev/peps/pep-0639/
[pip's documentation]: https://pip.pypa.io/en/stable/cli/pip_install/#vcs-support


Deprecated
----------

The `%{pyproject_build_lib}` macro is deprecated, don't use it.


Testing the macros
------------------

This repository has two kinds of tests.
First, there is RPM `%check` section, run when building the `python-rpm-macros`
package.

Then there are CI tests.
There is currently [no way to run Fedora CI tests locally][ci-rfe],
but you can do what the tests do manually using mock.
For each `$PKG.spec` in `tests/`:

  - clean your mock environment:

        mock -r fedora-rawhide-x86_64 clean

  - install the version of `python-rpm-macros` you're testing, e.g.:

        mock -r fedora-rawhide-x86_64 install .../python-rpm-macros-*.noarch.rpm

  - download the sources:

        spectool -g -R $PKG.spec

  - build a SRPM:

        rpmbuild -bs $PKG.spec

  - build in mock, using the path from the command above as `$SRPM`:

        mock -r fedora-rawhide-x86_64 -n -N $SRPM

[ci-rfe]: https://pagure.io/fedora-ci/general/issue/4
