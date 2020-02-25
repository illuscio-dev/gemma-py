import pytest
from dataclasses import dataclass, field
from typing import Any

from gemma import (
    Course,
    Compass,
    Surveyor,
    Cartographer,
    Coordinate,
    Fallback,
    Attr,
    Item,
    Call,
)


@dataclass
class TestData:
    a: str = "a data"
    b: str = "b data"
    one: int = 1
    two: int = 2
    dict_data: dict = field(default_factory=dict)
    list_data: list = field(default_factory=list)
    caller_set_value: Any = None

    def caller_set_tester(self, value: Any):
        self.caller_set_value = value


@dataclass
class DataSimple:
    a: str = "a data"
    b: str = "b data"
    one: int = 1
    two: int = 2
    _private: str = "whoops"


class DataCallable:
    def __init__(self):
        self.a: str = "a value"
        self.b: str = "b value"

    def get_a(self) -> str:
        return self.a + " called"

    def get_b(self) -> str:
        return self.b + " called"

    @staticmethod
    def one_static() -> int:
        return 1

    @classmethod
    def two_class(cls) -> int:
        return 2

    @staticmethod
    def _private() -> str:
        return "whoops"


class ThrowsKeyError:
    def __getitem__(self, item: Any):
        raise KeyError

    def __setitem__(self, key: Any, value: Any) -> Any:
        raise KeyError


class ThrowsIndexError:
    def __getitem__(self, item: Any):
        raise IndexError

    def __setitem__(self, key: Any, value: Any) -> Any:
        raise IndexError


class CartValueTransform(Cartographer):
    def clean_value(self, value: Any, coordinate: Coordinate) -> Any:
        return str(value) + " transformed"


def make_dict() -> dict:
    return {
        "a dict": "a value",
        "b dict": "b value",
        "one dict": 1,
        "two dict": 2,
        3: "three int",
        4: "four int",
    }


def make_list() -> list:
    return ["zero list", "one list", "two list", "three list", make_dict()]


@pytest.fixture
def data_dict() -> dict:
    return make_dict()


@pytest.fixture
def data_list(data_dict) -> list:
    return make_list()


@pytest.fixture
def data_structure_1() -> TestData:
    data = TestData(dict_data=make_dict(), list_data=make_list())
    return data


@pytest.fixture
def data_simple() -> DataSimple:
    return DataSimple()


@pytest.fixture
def data_callable() -> DataCallable:
    return DataCallable()


@pytest.fixture
def throws_key_error() -> ThrowsKeyError:
    return ThrowsKeyError()


@pytest.fixture
def throws_index_error() -> ThrowsIndexError:
    return ThrowsIndexError()


@pytest.fixture
def course_empty() -> Course:
    return Course()


@pytest.fixture
def course_basic() -> Course:
    return Course(Fallback("a"), Fallback("b"), Fallback("c"), Fallback("d"))


@pytest.fixture
def course_types():
    return Course(Fallback("a"), Attr("b"), Item("c"), Call("d"))


@pytest.fixture
def compass_generic():
    return Compass()


@pytest.fixture
def surveyor_generic():
    return Surveyor()


@pytest.fixture
def cartographer_generic():
    return Cartographer()


@pytest.fixture
def cartographer_transform_value():
    return CartValueTransform()


@pytest.fixture
def photo_info():
    return {"width": 1920, "height": 1080, "aspect": "16:9", "resolution": "1280x720"}
