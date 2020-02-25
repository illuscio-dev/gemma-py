import venv
import sys
import pathlib

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


def create_venv(lib_name: str, py_version: str) -> pathlib.Path:
    """
    creates the new virtual environment
    :param lib_name: name of library
    :param py_version: string representation of two-digit python version (ie 37)
    :return: path to venv
    """

    venv_name = f"{lib_name}-py-{py_version}"
    venv_path = pathlib.Path(f"~/venvs/{venv_name}").expanduser()

    try:
        venv_path.mkdir(parents=True, exist_ok=False)
    except FileExistsError as error:
        raise error

    venv.create(env_dir=str(venv_path), with_pip=True, system_site_packages=True)

    return venv_path


def register_venv(activate_path: pathlib.Path, lib_name: str, py_version: str) -> str:
    """
    registers the new enviroment with a .bashrc entry alias for easy venv entry
    :param activate_path: path to virtual env activation script
    :param py_version: string representation of two-digit python version (ie 37)
    :param lib_name: name of library
    :return: bash alias to enter venv
    """

    lib_path: pathlib.Path = (pathlib.Path(__file__).parent.parent.parent.absolute())

    bash_alias = f"env_{lib_name}-{py_version}"

    command = f'alias {bash_alias}=\'cd "{lib_path}";source "{activate_path}"\''

    bash_rc_path = pathlib.Path("~/.bash_profile").expanduser()
    bash_rc_text = bash_rc_path.read_text()

    if command in bash_rc_text:
        return bash_alias

    bash_rc_text += (
        f"\n"
        f"\n# {lib_name} development virtual env entry for Python {py_version}"
        f"\n{command}"
    )

    with bash_rc_path.open(mode="w") as f:
        f.write(bash_rc_text)

    return bash_alias


def main() -> None:
    """makes virtual enviroment for development and adds alias to ~/.bashrc"""

    py_version = f"{sys.version_info[0]}{sys.version_info[1]}"

    config = load_cfg()
    lib_name = config.get("metadata", "name")

    venv_path = create_venv(lib_name, py_version)
    activate_path = venv_path / "bin" / "activate"

    bash_alias = register_venv(activate_path, lib_name, py_version)

    sys.stdout.write(str(bash_alias))


if __name__ == "__main__":
    """creates virtual enviroment and writes path to stdout"""
    main()
