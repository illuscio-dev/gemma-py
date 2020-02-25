import pytest
from typing import Any

from gemma import Fallback, Attr, Item, Call, NullNameError, BearingAbstract, bearing


# ##### HELPER CLASSES #####
class MultiArg(list):
    """used for testing Call.place with args"""

    def cast_append(self, value, cast_type=None):
        try:
            value = cast_type(value)
        except (TypeError, ValueError):
            pass

        self.append(value)

    def args_reversed(self, cast_type=None, value=None):
        self.cast_append(value, cast_type)


class Alpha(BearingAbstract):
    """used for testing equality and sorting between bearing types"""

    def __str__(self) -> str:
        raise NotImplementedError

    def fetch(self, target: Any) -> Any:
        raise NotImplementedError

    def place(self, target: Any, value: Any) -> None:
        raise NotImplementedError


class Beta(BearingAbstract):
    """used for testing equality and sorting between bearing types"""

    def __str__(self) -> str:
        raise NotImplementedError

    def fetch(self, target: Any) -> Any:
        raise NotImplementedError

    def place(self, target: Any, value: Any) -> None:
        raise NotImplementedError


# ##### TESTS #####
def test_not_implemented_errors():
    with pytest.raises(NotImplementedError):
        BearingAbstract("a").__str__()
    with pytest.raises(NotImplementedError):
        BearingAbstract("a").fetch(dict())
    with pytest.raises(NotImplementedError):
        BearingAbstract("a").place(dict(), "value")


class TestCasting:
    def test_factory_stays(self):
        this_attr = Attr("a", factory=dict)
        assert this_attr.factory_type == dict

    def test_init_type_raises(self):
        with pytest.raises(TypeError):
            Attr(1)

    def test_bearing_from_string(self):
        this_bearing = Fallback("[test]")
        assert this_bearing.name == "[test]"

    def test_attr_from_string(self):
        this_bearing = Attr.name_from_str("@test")
        assert this_bearing == "test"

    def test_item_from_string(self):
        this_bearing = Item.name_from_str("[test]")
        assert this_bearing == "test"

    def test_caller_from_string(self):
        this_bearing = Call.name_from_str("test()")
        assert this_bearing == "test"

    def test_attr_from_string_raises(self):
        with pytest.raises(ValueError):
            Attr.name_from_str("[test]")

    def test_item_from_string_raises(self):
        with pytest.raises(ValueError):
            Item.name_from_str("@test")

    def test_caller_from_string_raises(self):
        with pytest.raises(ValueError):
            Call.name_from_str("@test")

    def test_bearing_from_bearing(self):
        this_bearing = Attr(Item("name"))
        assert this_bearing.name == "name"
        assert isinstance(this_bearing, Attr)

    def test_bearings_from_bearing_raises(self):
        bearing1 = Item(1)

        with pytest.raises(TypeError):
            Attr(bearing1)

    @pytest.mark.parametrize(
        "name, correct_type",
        [
            (1, Item),
            ("[1]", Item),
            ("@a", Attr),
            ("1", Fallback),
            ("[item]", Item),
            ("callable()", Call),
            ("a", Fallback),
        ],
    )
    def test_bearing_func(self, name, correct_type):
        assert isinstance(bearing(name), correct_type)

    @pytest.mark.parametrize("name", [1])
    def test_bearing_func_raises(self, name):
        with pytest.raises(TypeError):
            bearing(name, bearing_classes=[Attr])

    def test_init_factory_raises(self):
        with pytest.raises(TypeError):
            Item(1).init_factory()


class TestStrRepr:
    def test_bearing_str(self):
        assert str(Fallback("a")) == "a"

    def test_attr_str(self):
        assert str(Attr("a")) == "@a"

    def test_item_str(self):
        assert str(Item("a dict")) == "[a dict]"

    def test_caller_str(self):
        assert str(Call("keys")) == "keys()"

    def test_bearing_repr(self):
        assert repr(Fallback("a")) == "<Fallback: 'a'>"

    def test_bearing_repr_int(self):
        assert repr(Fallback(1)) == "<Fallback: 1>"

    def test_bearing_repr_factory(self):
        assert repr(Item("a", factory=dict)) == "<Item: 'a', factory=dict>"


class TestFetch:
    def test_bearing_fetch_attr(self, data_structure_1):
        assert Fallback("a").fetch(data_structure_1) == "a data"
        assert Fallback("b").fetch(data_structure_1) == "b data"

    def test_bearing_fetch_index(self, data_list):
        assert Fallback(0).fetch(data_list) == "zero list"
        assert Fallback(1).fetch(data_list) == "one list"
        assert Fallback(2).fetch(data_list) == "two list"
        assert Fallback(3).fetch(data_list) == "three list"

    def test_bearing_fetch_item_str(self, data_dict):
        assert Fallback("a dict").fetch(data_dict) == "a value"
        assert Fallback("b dict").fetch(data_dict) == "b value"
        assert Fallback("one dict").fetch(data_dict) == 1
        assert Fallback("two dict").fetch(data_dict) == 2

    def test_bearing_fetch_item_int(self, data_dict):
        assert Fallback(3).fetch(data_dict) == "three int"
        assert Fallback(4).fetch(data_dict) == "four int"

    def test_bearing_fetch_callable(self, data_dict):
        assert list(Fallback("keys").fetch(data_dict)) == [
            "a dict",
            "b dict",
            "one dict",
            "two dict",
            3,
            4,
        ]

    def test_attr_fetch(self, data_structure_1):
        assert Attr("a").fetch(data_structure_1) == "a data"
        assert Attr("b").fetch(data_structure_1) == "b data"

    def test_item_fetch(self, data_dict):
        assert Item("a dict").fetch(data_dict) == "a value"
        assert Item("b dict").fetch(data_dict) == "b value"

    def test_caller_fetch(self, data_dict):
        assert list(Call("keys").fetch(data_dict)) == [
            "a dict",
            "b dict",
            "one dict",
            "two dict",
            3,
            4,
        ]

    def test_bearing_fetch_raises(self, data_dict):
        with pytest.raises(NullNameError):
            Fallback("c").fetch(data_dict)

    def test_bearing_fetch_raises_key(self, throws_key_error):
        with pytest.raises(NullNameError):
            Fallback("c").fetch(throws_key_error)

    def test_bearing_fetch_raises_index(self, throws_index_error):
        with pytest.raises(NullNameError):
            Fallback(1).fetch(throws_index_error)

    def test_attr_fetch_raises(self, data_structure_1):
        with pytest.raises(NullNameError):
            Attr("c").fetch(data_structure_1)

    def test_item_fetch_raises_null_name_dict(self, data_dict):
        with pytest.raises(NullNameError):
            Item("c").fetch(data_dict)

    def test_item_fetch_raises_null_name_list(self, data_list):
        with pytest.raises(NullNameError):
            Item(7).fetch(data_list)

    def test_item_fetch_raises_type_list(self, data_list):
        with pytest.raises(TypeError):
            Item("c").fetch(data_list)

    def test_item_fetch_raises_type_dataclass(self, data_structure_1):
        with pytest.raises(TypeError):
            Item("c").fetch(data_structure_1)

    def test_caller_fetch_raises(self, data_structure_1):
        with pytest.raises(NullNameError):
            Call("c").fetch(data_structure_1)


class TestPlace:
    def test_bearing_place_attr(self, data_structure_1):
        Fallback("a").place(data_structure_1, "changed value")
        assert data_structure_1.a == "changed value"

    def test_bearing_place_item(self, data_dict):
        Fallback("a dict").place(data_dict, "changed value")
        assert data_dict["a dict"] == "changed value"

    def test_bearing_place_call(self, data_structure_1):
        Fallback("caller_set_tester").place(data_structure_1, "changed value")
        assert data_structure_1.caller_set_value == "changed value"

    def test_attr_place(self, data_structure_1):
        Attr("a").place(data_structure_1, "changed value")
        assert data_structure_1.a == "changed value"

    def test_item_place(self, data_dict):
        Item("a dict").place(data_dict, "changed value")
        assert data_dict["a dict"] == "changed value"

    def test_caller_place(self, data_structure_1):
        Call("caller_set_tester").place(data_structure_1, "changed value")
        assert data_structure_1.caller_set_value == "changed value"

    def test_caller_place_arg(self):
        data_list = MultiArg(("zero", "one", "two"))
        casts_str = Call("cast_append", func_args=(str,))
        casts_str.place(data_list, 3)
        assert data_list == ["zero", "one", "two", "3"]

    def test_caller_place_kwarg(self,):
        data_list = MultiArg(("zero", "one", "two"))
        casts_str = Call("cast_append", func_kwargs={"cast_type": str})
        casts_str.place(data_list, 3)
        assert data_list == ["zero", "one", "two", "3"]

    def test_caller_place_arg_replace(self,):
        data_list = ["zero", "one", "two"]
        inserts_head = Call("insert", func_args=(0, Call.VALUE_ARG))
        inserts_head.place(data_list, "new")
        assert data_list == ["new", "zero", "one", "two"]

    def test_caller_place_kwarg_replace(self,):
        data_list = MultiArg(("zero", "one", "two"))
        inserts_head = Call(
            "args_reversed", func_kwargs={"value": Call.VALUE_ARG, "cast_type": str}
        )
        inserts_head.place(data_list, 3)
        assert data_list == ["zero", "one", "two", "3"]

    def test_bearing_place_raises(self, data_structure_1):
        with pytest.raises(NullNameError):
            Fallback("c").place(data_structure_1, "changed value")

    def test_bearing_place_raises_type(self, data_structure_1):
        with pytest.raises(NullNameError):
            Fallback(1).place(data_structure_1, "changed value")

    def test_attr_place_raises(self, data_structure_1):
        with pytest.raises(NullNameError):
            Attr("c").place(data_structure_1, "changed value")

    def test_attr_place_raises_type(self, data_structure_1):
        with pytest.raises(TypeError):
            Attr("caller_set_tester").place(data_structure_1, "changed value")
        assert data_structure_1.caller_set_tester.__name__ == "caller_set_tester"
        assert callable(data_structure_1.caller_set_tester)

    def test_item_place_raises_key(self, throws_key_error):
        with pytest.raises(NullNameError):
            Item("a").place(throws_key_error, "changed value")

    def test_item_place_raises_index(self, throws_index_error):
        with pytest.raises(NullNameError):
            Item(1).place(throws_index_error, "changed value")

    def test_item_place_raises_type(self, data_structure_1):
        with pytest.raises(TypeError):
            Item("a").place(data_structure_1, "changed value")

    def test_item_place_fill_list(self,):
        data_list = list()
        Item(3).place(data_list, "new value")
        assert data_list == [None, None, None, "new value"]

    def test_item_place_list_exists(self,):
        data_list = [0, 1, 2, 3]
        Item(3).place(data_list, "new value")
        assert data_list == [0, 1, 2, "new value"]

    def test_caller_place_raises(self, data_structure_1):
        with pytest.raises(NullNameError):
            Call("c").place(data_structure_1, "changed value")

    def test_caller_place_raises_type(self, data_structure_1):
        with pytest.raises(TypeError):
            Call("b").place(data_structure_1, "changed value")
        assert data_structure_1.b == "b data"


class TestComparisons:
    def test_equality(self):
        assert Fallback("a") == Fallback("a")
        assert Attr("a") == Attr("a")
        assert Item("a") == Item("a")
        assert Call("a") == Call("a")

    def test_not_equal(self):
        assert Fallback("a") != Fallback("b")
        assert Attr("a") != Attr("b")
        assert Item("a") != Item("b")
        assert Call("a") != Call("b")

    def test_not_equal_type(self):
        with pytest.raises(TypeError):
            assert Attr("a") == "a"

    def test_equality_type_diff(self):
        assert Fallback("a") == Item("a")
        assert Fallback("a") == Attr("a")
        assert Fallback("a") == Call("a")
        assert Item("a") == Fallback("a")
        assert Attr("a") == Fallback("a")
        assert Call("a") == Fallback("a")

    def test_not_equal_type_value_diff(self):
        assert Fallback("a") != Item("b")
        assert Fallback("a") != Attr("b")
        assert Fallback("a") != Call("b")
        assert Item("a") != Fallback("b")
        assert Attr("a") != Fallback("b")
        assert Call("a") != Fallback("b")

    def test_not_equal_type_diff(self):
        assert Item("a") != Attr("a")
        assert Item("a") != Call("a")
        assert Attr("a") != Item("a")
        assert Attr("a") != Call("a")
        assert Call("a") != Attr("a")
        assert Call("a") != Item("a")

    def test_not_equal_bearing_custom(self):
        assert Fallback("a") != Alpha("a")

    def test_equal_bearing_custom(self):
        new_bearing = bearing("a", [Item, Fallback, Alpha])
        assert new_bearing == Alpha("a")

    def test_comparisons(self):
        assert Fallback("a") <= Fallback("a")
        assert Fallback("a") <= Fallback("b")
        assert Fallback("a") < Fallback("b")
        assert Fallback("b") >= Fallback("b")
        assert Fallback("b") >= Fallback("a")
        assert Fallback("b") > Fallback("a")

    def test_comparison_types(self):
        assert Item("a") < Fallback("a")
        assert Item("a") <= Fallback("a")
        assert Item("a") < Call("a")
        assert Item("a") <= Call("a")
        assert Item("a") < Attr("a")
        assert Item("a") <= Attr("a")
        assert Item("a") <= Item("a")
        assert Item("a") < Attr("a") < Call("a") < Fallback("a")
        assert Item("a") <= Attr("a") <= Call("a") <= Fallback("a")

        assert Fallback("a") > Item("a")
        assert Fallback("a") >= Item("a")
        assert Fallback("a") > Attr("a")
        assert Fallback("a") >= Attr("a")
        assert Fallback("a") > Call("a")
        assert Fallback("a") >= Call("a")
        assert Fallback("a") >= Fallback("a")
        assert Fallback("a") > Call("a") > Attr("a") > Item("a")
        assert Fallback("a") >= Call("a") >= Attr("a") >= Item("a")

    def test_comparison_custom_types(self):
        assert (
            Fallback("a") > Beta("a") > Alpha("a") > Call("a") > Attr("a") > Item("a")
        )
        assert (
            Fallback("a")
            >= Beta("a")
            >= Alpha("a")
            > Call("a")
            >= Attr("a")
            >= Item("a")
        )

        assert (
            Item("a") < Attr("a") < Call("a") < Alpha("a") < Beta("a") < Fallback("a")
        )
        assert (
            Item("a")
            <= Attr("a")
            <= Call("a")
            <= Alpha("a")
            <= Beta("a")
            <= Fallback("a")
        )


def test_sort_bearings():
    bearing_unsorted = [
        Fallback("b"),
        Call("b"),
        Alpha("b"),
        Attr("b"),
        Fallback("a"),
        Item("b"),
        Call("a"),
        Beta("b"),
        Alpha("a"),
        Attr("a"),
        Item("a"),
        Attr("a"),
        Beta("a"),
    ]

    bearing_sorted = [
        Item("a"),
        Item("b"),
        Attr("a"),
        Attr("a"),
        Attr("b"),
        Call("a"),
        Call("b"),
        Alpha("a"),
        Alpha("b"),
        Beta("a"),
        Beta("b"),
        Fallback("a"),
        Fallback("b"),
    ]

    assert sorted(bearing_unsorted) == bearing_sorted
