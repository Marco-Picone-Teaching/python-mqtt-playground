from pathlib import Path
from typing import Any

import yaml


class ConfigManager:
    """
    ConfigManager class loads the configuration shared by all the playground scripts
    (e.g., MQTT Broker host and port) from a YAML file.

    By default, the file `config.yaml` is searched in the current working directory and,
    if not found, in the project root directory.
    """

    # Default name of the configuration file
    DEFAULT_CONFIG_FILE_NAME = "config.yaml"

    # Project root directory: src/mqtt_playground/config/config_manager.py -> 3 levels up
    PROJECT_ROOT_DIR = Path(__file__).resolve().parents[3]

    # Default values used when a parameter is not defined in the configuration file
    DEFAULT_BROKER_HOST = "127.0.0.1"
    DEFAULT_BROKER_PORT = 1883
    DEFAULT_BROKER_KEEPALIVE = 60

    def __init__(self, config_file_path: str | Path | None = None) -> None:
        """
        Constructor for ConfigManager class
        :param config_file_path: Path of the YAML configuration file. If None the default file is used
        """

        if config_file_path is None:
            config_file_path = self._find_default_config_file()

        self.config_file_path: Path = Path(config_file_path)

        # Load the configuration file into a Python dictionary
        with open(self.config_file_path, "r", encoding="utf-8") as config_file:
            self._config: dict[str, Any] = yaml.safe_load(config_file) or {}

    @classmethod
    def _find_default_config_file(cls) -> Path:
        """ Search the default configuration file in the current working directory and in the project root """

        candidate_paths = [Path.cwd() / cls.DEFAULT_CONFIG_FILE_NAME,
                           cls.PROJECT_ROOT_DIR / cls.DEFAULT_CONFIG_FILE_NAME]

        for candidate_path in candidate_paths:
            if candidate_path.is_file():
                return candidate_path

        raise FileNotFoundError(f"Configuration file not found. Searched in: {[str(p) for p in candidate_paths]}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Read a configuration value using a dotted key (e.g., "broker.host")
        :param key: Dotted path of the configuration parameter
        :param default: Value returned if the parameter is not defined
        :return: The configuration value or the default one
        """

        value: Any = self._config
        for key_part in key.split("."):
            if not isinstance(value, dict) or key_part not in value:
                return default
            value = value[key_part]

        return value

    @property
    def broker_host(self) -> str:
        """ Host (IP address or hostname) of the target MQTT Broker """
        return str(self.get("broker.host", self.DEFAULT_BROKER_HOST))

    @property
    def broker_port(self) -> int:
        """ Port of the target MQTT Broker """
        return int(self.get("broker.port", self.DEFAULT_BROKER_PORT))

    @property
    def broker_keepalive(self) -> int:
        """ Keep Alive interval in seconds of the MQTT connection """
        return int(self.get("broker.keepalive", self.DEFAULT_BROKER_KEEPALIVE))
