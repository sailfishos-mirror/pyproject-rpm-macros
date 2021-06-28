from pathlib import Path
import importlib.metadata
import io

import pytest
import yaml

from pyproject_buildrequires import generate_requires


testcases = {}
with Path(__file__).parent.joinpath('pyproject_buildrequires_testcases.yaml').open() as f:
    testcases = yaml.safe_load(f)


@pytest.mark.parametrize('case_name', testcases)
def test_data(case_name, capsys, tmp_path, monkeypatch):
    case = testcases[case_name]

    cwd = tmp_path.joinpath('cwd')
    cwd.mkdir()
    monkeypatch.chdir(cwd)

    if case.get('xfail'):
        pytest.xfail(case.get('xfail'))

    for filename in case:
        file_types = ('.toml', '.py', '.in', '.ini', '.txt')
        if filename.endswith(file_types):
            cwd.joinpath(filename).write_text(case[filename])

    def get_installed_version(dist_name):
        try:
            return str(case['installed'][dist_name])
        except (KeyError, TypeError):
            raise importlib.metadata.PackageNotFoundError(
                f'info not found for {dist_name}'
            )
    requirement_files = case.get('requirement_files', [])
    requirement_files = [open(f) for f in requirement_files]
    try:
        generate_requires(
            get_installed_version=get_installed_version,
            include_runtime=case.get('include_runtime', False),
            extras=case.get('extras', []),
            toxenv=case.get('toxenv', None),
            generate_extras=case.get('generate_extras', False),
            requirement_files=requirement_files,
            use_build_system=case.get('use_build_system', True),
        )
    except SystemExit as e:
        assert e.code == case['result']
    except Exception as e:
        if 'except' not in case:
            raise
        assert type(e).__name__ == case['except']
    else:
        assert 0 == case['result']

        captured = capsys.readouterr()
        assert captured.out == case['expected']
    finally:
        for req in requirement_files:
            req.close()
