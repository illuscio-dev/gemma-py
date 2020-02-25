import pytest
from typing import List
from fractions import Fraction

from gemma import Compass, Item, Attr, Call, NonNavigableError


def test_compass_type_passes():
    compass = Compass()
    assert compass.is_navigable(dict())
    assert compass.is_navigable(list())
    assert compass.is_navigable(str())
    assert compass.is_navigable(int())


def test_compass_type_passes_single():
    compass = Compass(target_types=dict)
    assert compass.is_navigable(dict()) is True


def test_compass_type_fails_single():
    compass = Compass(target_types=dict)
    assert compass.is_navigable(list()) is False


def test_compass_type_passes_double():
    compass = Compass(target_types=(dict, List))
    assert compass.is_navigable(dict()) is True
    assert compass.is_navigable(list((1, 2))) is True


def test_compass_type_fails_double():
    compass = Compass(target_types=(dict, List))
    assert compass.is_navigable("one") is False
    assert compass.is_navigable(4) is False


def test_compass_bearings_raises_navigable_error():
    compass = Compass(target_types=list)
    with pytest.raises(NonNavigableError):
        compass.bearings(dict())


def test_dict_bearings(compass_generic, data_dict):
    assert compass_generic.bearings(data_dict) == [
        (Item("a dict"), "a value"),
        (Item("b dict"), "b value"),
        (Item("one dict"), 1),
        (Item("two dict"), 2),
        (Item(3), "three int"),
        (Item(4), "four int"),
    ]


def test_dict_bearings_limited(data_dict):
    compass = Compass(items=["a dict", "one dict", 4])
    assert compass.bearings(data_dict) == [
        (Item("a dict"), "a value"),
        (Item("one dict"), 1),
        (Item(4), "four int"),
    ]


def test_dict_bearings_items_false(data_dict):
    compass = Compass(items=False)
    assert compass.bearings(data_dict) == []


def test_list_bearings(compass_generic, data_list):
    assert compass_generic.bearings(data_list[:-1]) == [
        (Item(0), "zero list"),
        (Item(1), "one list"),
        (Item(2), "two list"),
        (Item(3), "three list"),
    ]


def test_list_bearings_limited(data_list):
    compass = Compass(items=[1, 3])
    assert compass.bearings(data_list[:-1]) == [
        (Item(1), "one list"),
        (Item(3), "three list"),
    ]


def test_dataclass_bearings(compass_generic, data_simple):
    assert compass_generic.bearings(data_simple) == [
        (Attr("a"), "a data"),
        (Attr("b"), "b data"),
        (Attr("one"), 1),
        (Attr("two"), 2),
    ]


def test_dataclass_bearings_limited(data_simple):
    compass = Compass(attrs=["b", "one"])
    assert compass.bearings(data_simple) == [(Attr("b"), "b data"), (Attr("one"), 1)]


def test_dict_bearings_with_callers(data_dict):
    compass = Compass(items=False, calls=["keys"])
    assert compass.bearings(data_dict) == [(Call("keys"), data_dict.keys())]


def test_dataclass_all_callers(data_callable):
    compass = Compass(calls=True)
    assert compass.bearings(data_callable) == [
        (Attr("a"), "a value"),
        (Attr("b"), "b value"),
        (Call("get_a"), "a value called"),
        (Call("get_b"), "b value called"),
        (Call("one_static"), 1),
        (Call("two_class"), 2),
    ]


def test_inherited_compass(data_simple):
    class CompassNew(Compass):
        pass

    compass_new = CompassNew()
    assert compass_new.bearings(data_simple) == [
        (Attr("a"), "a data"),
        (Attr("b"), "b data"),
        (Attr("one"), 1),
        (Attr("two"), 2),
    ]


def test_not_implemented_iter(data_callable):
    class CompassLess(Compass):
        def attr_iter(self, target):
            raise NotImplementedError

    compass_less = CompassLess(calls=True)

    assert compass_less.bearings(data_callable) == [
        (Call("get_a"), "a value called"),
        (Call("get_b"), "b value called"),
        (Call("one_static"), 1),
        (Call("two_class"), 2),
    ]


def test_ignore_underscore_slots(compass_generic):
    data = Fraction("3/4")
    assert compass_generic.bearings(data) == []
