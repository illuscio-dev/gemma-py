import sys
import pathlib
import os
import shutil
import re
from itertools import count
from glob import iglob
from dataclasses import dataclass
from configparser import ConfigParser

"""
changes name of module in file path file path directory and all relevant config settings
"""


@dataclass(init=False)
class ScriptInfo:
    """
    class for holding script parameters and moving data between functions
    """

    # names
    name_target: str = None
    name_original: str = None

    # paths
    path_original: pathlib.Path = None
    path_target: pathlib.Path = None

    # flags
    new_created: bool = False

    @staticmethod
    def config_path() -> pathlib.Path:
        """path to configuration file in current working directory"""
        return pathlib.Path("./setup.cfg").absolute()


def load_cfg(config_path: pathlib.Path) -> ConfigParser:
    """
    loads library config file
    :return: loaded `ConfigParser` object
    """
    config = ConfigParser()
    config.read(str(config_path))
    return config


def load_target_name(script_info: ScriptInfo) -> None:
    """
    loads target name from system arguments into script info, raises errors if value is
    incorrect
    :param script_info:
    :return:
    """
    # throw error if new name was not passed
    try:
        script_info.name_target = sys.argv[1]
    except IndexError:
        raise ValueError("new name must be passed with name=[name] param")

    # throw error if target name is empty
    if not script_info.name_target:
        raise ValueError("new name must be passed with name=[name] param")


def make_new_directory(script_info: ScriptInfo) -> None:

    # load current and new paths
    script_info.path_original = pathlib.Path(".").absolute()
    script_info.path_target = (
        script_info.path_original.parent / f"{script_info.name_target}-py"
    )

    # throw error if new library directory already exists
    if script_info.path_target.exists():
        raise FileExistsError(f"directory {script_info.path_target} exists")

    # create new directory and copy current contents
    shutil.copytree(str(script_info.path_original), str(script_info.path_target))

    # switch this flag to show the high-level error catcher that the new directory
    # has been made and will need to be removed in cleanup of a later exception is
    # caught
    script_info.new_created = True


def edit_cfg(script_info: ScriptInfo) -> str:
    """
    edits setup.cfg with new name of library in necessary fields

    :param script_info: script info object
    """
    target_name = script_info.name_target

    config = load_cfg(script_info.config_path())
    old_name = config.get("metadata", "name")

    config.set("metadata", "name", target_name)
    config.set("coverage:run", "source", target_name)
    config.set("coverage:html", "title", f"coverage report for {target_name}")
    config.set("build_sphinx", "project", target_name)

    with open(str(script_info.config_path()), mode="w") as f:
        config.write(f)

    return old_name


def rewrite_sphinx_conf(target_name: str) -> None:
    """
    writes sphinx conf.py with new lib name for documentation settings
    :param target_name: new name of library
    :return:
    """

    # there is template file we can perform a simple find/replace on to change the
    # name of the lib where necessary
    template_path = pathlib.Path("./zdocs/source/conf-template").absolute()
    conf_path = pathlib.Path("./zdocs/source/conf.py").absolute()

    template_text = template_path.read_text()
    conf_text = template_text.replace("{lib-name-goes-here}", target_name)

    conf_path.write_text(conf_text)


def rename_packages(old_name: str, target_name: str) -> None:
    """
    renames top level directory, module package, and changes active directory to it
    :param old_name: old name of lib
    :param target_name: new name of lib
    :return:
    """
    # find current lib path - look for the init and ignore zdevelop
    search_pattern = "./*/__init__.py"

    # iterate through init statements in current directory and rename parents
    i = None
    for init_path, i in zip(iglob(search_pattern, recursive=True), count(1)):

        parent_path: pathlib.Path = pathlib.Path(init_path).parent
        parent_name = parent_path.name

        if parent_name.lower() == "zdevelop":
            continue

        # if this lib has multiple packages, we may need to sub-out the name
        if old_name.lower() in parent_name.lower():
            new_name = re.sub(parent_name, old_name, target_name, flags=re.IGNORECASE)
        # otherwise, if the name is unrelated it just gets renamed to the new one
        else:
            new_name = target_name

        target_path = parent_path.with_name(new_name)

        # rename module folder name
        try:
            parent_path.rename(target_path)
        except FileExistsError as this_error:
            sys.stderr.write(
                f"package '{target_name}' already exists, your current package names"
                f"may not conform to illuscio's standards. All packages names should "
                f"contain the root name of the library"
            )
            raise this_error

    if i is None:
        raise FileNotFoundError("no packages found in library")


def alter_new(script_info: ScriptInfo) -> None:
    """
    renames lib and writes 1 or 0 to stdout for whether .egg needs to be
    rewritten
    """

    # edit the config file and get current name
    old_name = edit_cfg(script_info)

    # write new conf.py
    rewrite_sphinx_conf(script_info.name_target)

    # remove .egg info
    path_egg = f"{old_name}.egg-info"
    try:
        shutil.rmtree(path_egg)
    except PermissionError:
        os.chmod(path_egg, mode=0o007)
        shutil.rmtree(path_egg)
    except FileNotFoundError:
        pass

    # rename directory
    rename_packages(old_name, script_info.name_target)


def main():
    """makes new directory and handles errors"""

    script_info = ScriptInfo()

    try:
        # cor logic of the script, wrapped in try/except to handle directory cleanup
        load_target_name(script_info)

        make_new_directory(script_info)

        # change working directory to new directory
        os.chdir(str(script_info.path_target))

        # make alterations to new directory
        alter_new(script_info)

        # write result path to srd out so make file can change working directory
        sys.stdout.write(str(script_info.path_target))

    except BaseException as this_error:
        # if there are any errors and the new directory path was created during this
        # script, we need to clean it up before aborting
        if script_info.new_created:
            shutil.rmtree(str(script_info.path_target))
        raise this_error
    else:
        # if all alterations to the new directory go as planned, we can remove the old
        # directory
        shutil.rmtree(str(script_info.path_original))


if __name__ == "__main__":

    try:
        main()
    except BaseException as error:
        # tell Make script not to continue
        sys.stdout.write("0")
        raise error
