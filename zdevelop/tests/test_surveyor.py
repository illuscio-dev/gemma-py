import pytest
from dataclasses import dataclass

from gemma import (
    Surveyor,
    Course,
    Attr,
    Item,
    Compass,
    NonNavigableError,
    Call,
    SuppressedErrors,
    PORT,
)


def test_surveyor_chart_raises_navigable():
    compass = Compass(target_types=dict)
    surveyor = Surveyor(compasses=[compass])

    with pytest.raises(NonNavigableError):
        surveyor.chart([1, 2, 3])


def test_surveyor_suppress_error():
    compass = Compass(target_types=dict)
    surveyor = Surveyor(compasses=[compass])

    data = {"a": "a value", "list": [1, 2, 3], "list2": [1, 2, 3], "b": "b value"}

    courses = list()
    raised = None

    with pytest.raises(SuppressedErrors):
        try:
            for x in surveyor.chart_iter(data, exceptions=False):
                courses.append(x)
        except SuppressedErrors as error:
            raised = error
            raise error

    assert len(raised.errors) == 2
    assert isinstance(raised.errors[0], NonNavigableError)
    assert isinstance(raised.errors[1], NonNavigableError)

    assert courses == [
        (PORT / "[a]", "a value"),
        (PORT / "list", [1, 2, 3]),
        (PORT / "list2", [1, 2, 3]),
        (PORT / "[b]", "b value"),
    ]


def test_surveyor_chart_simple(
    surveyor_generic: Surveyor, data_simple, course_empty: Course
):
    assert surveyor_generic.chart(data_simple) == [
        (course_empty / Attr("a"), "a data"),
        (course_empty / Attr("b"), "b data"),
        (course_empty / Attr("one"), 1),
        (course_empty / Attr("two"), 2),
    ]


def test_surveyor_chart_nested(
    data_structure_1,
    surveyor_generic: Surveyor,
    course_empty: Course,
    data_dict: dict,
    data_list: list,
):
    root = course_empty

    assert surveyor_generic.chart(data_structure_1) == [
        (root / Attr("a"), "a data"),
        (root / Attr("b"), "b data"),
        (root / Attr("one"), 1),
        (root / Attr("two"), 2),
        (root / Attr("dict_data"), data_dict),
        (root / Attr("dict_data") / Item("a dict"), "a value"),
        (root / Attr("dict_data") / Item("b dict"), "b value"),
        (root / Attr("dict_data") / Item("one dict"), 1),
        (root / Attr("dict_data") / Item("two dict"), 2),
        (root / Attr("dict_data") / Item(3), "three int"),
        (root / Attr("dict_data") / Item(4), "four int"),
        (root / Attr("list_data"), data_list),
        (root / Attr("list_data") / Item(0), "zero list"),
        (root / Attr("list_data") / Item(1), "one list"),
        (root / Attr("list_data") / Item(2), "two list"),
        (root / Attr("list_data") / Item(3), "three list"),
        (root / Attr("list_data") / Item(4), data_dict),
        (root / Attr("list_data") / Item(4) / Item("a dict"), "a value"),
        (root / Attr("list_data") / Item(4) / Item("b dict"), "b value"),
        (root / Attr("list_data") / Item(4) / Item("one dict"), 1),
        (root / Attr("list_data") / Item(4) / Item("two dict"), 2),
        (root / Attr("list_data") / Item(4) / Item(3), "three int"),
        (root / Attr("list_data") / Item(4) / Item(4), "four int"),
        (root / Attr("caller_set_value"), None),
    ]


def test_surveyor_chart_callable(data_callable, course_empty):

    compass = Compass(target_types=type(data_callable), calls=["get_a", "two_class"])
    surveyor = Surveyor(compasses=[compass, Compass()])

    root = course_empty

    assert surveyor.chart(data_callable) == [
        (root / Attr("a"), "a value"),
        (root / Attr("b"), "b value"),
        (root / Call("get_a"), "a value called"),
        (root / Call("two_class"), 2),
    ]


def test_surveyor_add_endpoint():
    @dataclass
    class A:
        text: str = "string"

    data = {"one": 1, "two": 2, "a": A()}

    answer = [(PORT / "one", 1), (PORT / "two", 2), (PORT / "a", A())]

    surveyor = Surveyor(end_points_extra=(A,))
    assert surveyor.chart(data) == answer
