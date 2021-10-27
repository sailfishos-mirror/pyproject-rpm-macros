pyproject RPM macros
====================

These macros allow projects that follow the Python [packaging specifications]
to be packaged as RPMs.

They are still *provisional*: we can make non-backwards-compatible changes to
the API.
Please subscribe to Fedora's [python-devel list] if you use the macros.

They work for:

* traditional Setuptools-based projects that use the `setup.py` file,
* newer Setuptools-based projects that have a `setup.cfg` file,
* general Python projects that use the [PEP 517] `pyproject.toml` file (which allows using any build system, such as setuptools, flit or poetry).

These macros replace `%py3_build` and `%py3_install`, which only work with `setup.py`.

[packaging specifications]: https://packaging.python.org/specifications/
[python-devel list]: https://lists.fedoraproject.org/archives/list/python-devel@lists.fedoraproject.org/


Usage
-----

To use these macros, first BuildRequire them:

    BuildRequires: pyproject-rpm-macros

Also BuildRequire the devel package for the Python you are building against.
In Fedora, that's `python3-devel`.
(In the future, we plan to make `python3-devel` itself require
`pyproject-rpm-macros`.)

Next, you need to generate more build dependencies (of your projects and
the macros themselves) by running `%pyproject_buildrequires` in the
`%generate_buildrequires` section:

    %generate_buildrequires
    %pyproject_buildrequires

This will add build dependencies according to [PEP 517] and [PEP 518].
To also add run-time and test-time dependencies, see the section below.
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

To run tests in the `%check` section, the package's runtime dependencies
often need to also be included as build requirements.
This can be done using the `-r` flag:

    %generate_buildrequires
    %pyproject_buildrequires -r

For this to work, the project's build system must support the
[`prepare-metadata-for-build-wheel` hook](https://www.python.org/dev/peps/pep-0517/#prepare-metadata-for-build-wheel).
The popular buildsystems (setuptools, flit, poetry) do support it.

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

Note that both `-x` and `-t` imply `-r`,
because runtime dependencies are always required for testing.

[tox]: https://tox.readthedocs.io/
[tox-current-env]: https://github.com/fedora-python/tox-current-env/

Additionally to generated requirements you can supply multiple file names to `%pyproject_buildrequires` macro.
Dependencies will be loaded from them:

    %pyproject_buildrequires -r requirements/tests.in requirements/docs.in requirements/dev.in

For packages not using build system you can use `-N` to entirely skip automatical
generation of requirements and install requirements only from manually specified files.
`-N` option cannot be used in combination with other options mentioned above
(`-r`, `-e`, `-t`, `-x`).

Running tox based tests
-----------------------

In case you want to run the tests as specified in [tox] configuration,
you must use `%pyproject_buildrequires` with `-t` or `-e` as explained above.
Then, use the `%tox` macro in `%check`:

    %check
    %tox

The macro:

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
Only license files declared via [PEP 639] `License-Field` field are detected.
[PEP 639] is still a draft and can be changed in the future.

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
