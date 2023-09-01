import os
from json import dump

from dls_bba.configuration import LATTICE_SETTINGS, Configuration

OVERRIDES_NO_RELOAD = {"CONFIG_1": 1, "CONFIG_2": "str", "CONFIG_3": [4, 3, 2, 1]}
OVERRIDES_WITH_RELOAD = {
    LATTICE_SETTINGS[0]: 1,
    LATTICE_SETTINGS[1]: "str",
    LATTICE_SETTINGS[2]: [4, 3, 2, 1],
}


def test_config_getitem_uses_private_dictionary_as_expected():
    config = Configuration()
    assert isinstance(config, Configuration)
    assert isinstance(config._config, dict)
    config._config["TEST"] = 1
    assert config["TEST"] == 1


def test_config_returns_false_when_updated_with_args_that_do_not_require_reload():
    config = Configuration()
    assert not config.update_config(OVERRIDES_NO_RELOAD)
    for key, value in OVERRIDES_NO_RELOAD.items():
        assert config[key] == value


def test_config_returns_true_when_updated_with_args_that_do_require_reload():
    config = Configuration()
    assert config.update_config(OVERRIDES_WITH_RELOAD)
    for key, value in OVERRIDES_WITH_RELOAD.items():
        assert config[key] == value


def test_config_returns_false_when_updated_with_files_that_do_not_require_reload(
    tmp_path,
):
    config = Configuration()
    paths = []
    for i in range(3):
        filename = f"json_dump_{i}.json"
        filepath = os.path.join(tmp_path, filename)
        with open(filepath, "w") as fp:
            dump(OVERRIDES_NO_RELOAD, fp)
        paths.append(filepath)

    assert not config.apply_config_files(paths)
    for key, value in OVERRIDES_NO_RELOAD.items():
        assert config[key] == value


def test_config_returns_true_when_updated_with_files_that_do_require_reload(tmp_path):
    config = Configuration()
    paths = []
    for i in range(3):
        filename = f"json_dump_{i}.json"
        filepath = os.path.join(tmp_path, filename)
        with open(filepath, "w") as fp:
            dump(OVERRIDES_WITH_RELOAD, fp)
        paths.append(filepath)

    assert config.apply_config_files(paths)
    for key, value in OVERRIDES_WITH_RELOAD.items():
        assert config[key] == value


def test_default_config_is_applied_as_expected():
    config = Configuration()
    config.apply_default_config()
    assert len(config._config) >= 1
    for key in LATTICE_SETTINGS:
        assert key in config._config
        assert isinstance(config[key], (str, float, int, list, dict))


def test_default_config_is_applied_if_no_additional_files_are_given():
    config = Configuration.from_configuration_files(None)
    for key in LATTICE_SETTINGS:
        assert key in config._config
        assert isinstance(config[key], (str, float, int, list, dict))


def test_default_config_is_applied_first_if_additional_files_are_given(tmp_path):
    paths = []
    for i in range(3):
        filename = f"json_dump_{i}.json"
        filepath = os.path.join(tmp_path, filename)
        with open(filepath, "w") as fp:
            dump(OVERRIDES_WITH_RELOAD, fp)
        paths.append(filepath)

    config = Configuration.from_configuration_files(paths)
    for key in LATTICE_SETTINGS:
        assert key in config._config
        assert isinstance(config[key], (str, float, int, list, dict))
    for key, value in OVERRIDES_WITH_RELOAD.items():
        assert config[key] == value


def test_get_copy_of_current_config():
    config = Configuration.from_configuration_files(None)
    config_copy = config.get_settings()
    for key in config_copy.keys():
        assert config[key] == config_copy[key]
