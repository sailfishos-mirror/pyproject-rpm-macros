"""
This is a test backend for pyproject-rpm-macros' integration tests
It is not compliant with PEP 517 and omits some required hooks.
"""

from flit_core import buildapi

EXPECTED_CONFIG_SETTINGS = {"abc": "123", "xyz": "456", "--option-with-dashes": "1"}


def _verify_config_settings(config_settings):
    print(f"config_settings={config_settings}")
    if config_settings != EXPECTED_CONFIG_SETTINGS:
        raise ValueError(
            f"{config_settings!r} does not match expected {EXPECTED_CONFIG_SETTINGS!r}"
        )


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    _verify_config_settings(config_settings)
    return buildapi.build_wheel(wheel_directory, None, metadata_directory)


def get_requires_for_build_wheel(config_settings=None):
    _verify_config_settings(config_settings)
    return buildapi.get_requires_for_build_wheel(None)


def prepare_metadata_for_build_wheel(metadata_directory, config_settings=None):
    _verify_config_settings(config_settings)
    return buildapi.prepare_metadata_for_build_wheel(metadata_directory, None)
