import sys
import pathlib
from glob import iglob
from configparser import ConfigParser


CONFIG_PATH = pathlib.Path(__file__).parent.parent.parent / "setup.cfg"


def load_cfg() -> ConfigParser:
    """
    loads library config file
    :return: loaded `ConfigParser` object
    """
    config = ConfigParser()
    config.read(CONFIG_PATH)
    return config


if __name__ == "__main__":

    config: ConfigParser = load_cfg()
    version: str = config.get("bumpversion", "current_version")

    version_path_pattern: str = str(CONFIG_PATH.parent / "**" / "_version.py")
    version_file = next(iglob(version_path_pattern, recursive=True))

    with open(version_file, mode="w") as f:
        f.write(f'__version__ = "{version}"\n')

    sys.stdout.write(version)
