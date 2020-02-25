from dataclasses import dataclass, field
from typing import Tuple, Optional, Union, Dict, List


@dataclass
class DataSimple:
    text: Optional[str] = None
    number: Optional[int] = None


@dataclass
class DataStructured:
    a: Optional[str] = "a data"
    b: Optional[str] = "b data"
    one: Optional[int] = 31
    two: Optional[int] = 32
    dict_data: dict = field(default_factory=dict)
    list_data: list = field(default_factory=list)
    simple: DataSimple = field(default_factory=DataSimple)


@dataclass
class DataTarget:
    text_target: Optional[str] = None
    number_target: Optional[int] = None
    list_target: list = field(default_factory=list)
    dict_target: dict = field(default_factory=dict)


DataDictType = Dict[Union[int, str], Union[str, int, Dict[str, int], DataSimple]]

DataListType = List[Union[str, List[int], DataDictType, DataSimple]]


def _make_data_dict() -> DataDictType:

    data_dict: DataDictType = {
        "a": "a dict",
        "b": "b dict",
        1: "one dict",
        2: "two dict",
        "nested": {"one key": 1, "two key": 2},
        "simple": DataSimple("string value", 40),
    }

    return data_dict


def _make_data_list() -> DataListType:

    data_list: DataListType = [
        "zero list",
        "one list",
        "two list",
        "three list",
        _make_data_dict(),
        [10, 11, 12, 13],
        DataSimple("in a list", 20),
    ]

    return data_list


def test_objects() -> Tuple[
    DataSimple, DataDictType, DataListType, DataStructured, DataTarget
]:
    """
    returns fresh copies of data structure test objects.

    :return: ``simple``, ``data_dict``, ``data_list``, ``structured``, ``target``

    The structure of each object is detailed in ``gemma``'s documentation.
    """
    simple = DataSimple("simple text", 50)

    data_dict = _make_data_dict()
    data_list = _make_data_list()

    structured = DataStructured(
        dict_data=_make_data_dict(), list_data=_make_data_list()
    )

    target = DataTarget()

    return simple, data_dict, data_list, structured, target
