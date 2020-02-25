import pytest
from dataclasses import dataclass
from typing import Optional

from gemma import Course, PORT, Item, Fallback, Attr, Call, NullNameError


class TestBasicAPI:
    def test_init_basic(self, course_basic):
        assert str(course_basic) == "a/b/c/d"

    def test_repr(self, course_basic):
        assert repr(course_basic) == (
            "<Course: <Fallback: 'a'> / <Fallback: 'b'> / <Fallback: 'c'> "
            "/ <Fallback: 'd'>>"
        )

    def test_len(self, course_basic):
        assert len(course_basic) == 4

    def test_init_int(self):
        assert Course(1)[0] == Item(1)

    def test_concat_basic(self):
        course = PORT / "a" / "b" / "c" / "d"
        assert str(course) == "a/b/c/d"
        assert len(course) == 4

    def test_concat_multi_type(self):
        course = PORT / "a" / 1 / "c"
        assert str(course) == "a/[1]/c"
        assert isinstance(course[1], Item)

    def test_concat_courses(self):
        course = Course("a", "b") / Course("c", "d")
        assert str(course) == "a/b/c/d"
        assert len(course) == 4

    def test_concat_course_str(self):
        course = PORT / "a/[b]/c/d"
        assert len(course) == 4
        assert isinstance(course[1], Item)

    def test_replace_single(self):
        course = PORT / 0
        assert course.replace(0, 1) == PORT / 1

    @pytest.mark.parametrize(
        "index, value, answer",
        [
            (1, "key", PORT / 0 / "key" / 2 / 3),
            (0, "key", PORT / "key" / 1 / 2 / 3),
            (3, "key", PORT / 0 / 1 / 2 / "key"),
            (-1, "key", PORT / 0 / 1 / 2 / "key"),
            (-2, "key", PORT / 0 / 1 / "key" / 3),
            (slice(1, 3), "key", PORT / 0 / "key" / 3),
            (slice(1, 3), PORT / "key" / "sub-key", PORT / 0 / "key" / "sub-key" / 3),
            (slice(1, None), PORT / "key" / "sub-key", PORT / 0 / "key" / "sub-key"),
            (
                slice(None, 2),
                PORT / "key" / "sub-key",
                PORT / "key" / "sub-key" / 2 / 3,
            ),
        ],
    )
    def test_replace(self, index, value, answer):
        course = PORT / 0 / 1 / 2 / 3
        result = course.replace(index, value)
        print(f"resulting course {result}")
        assert result == answer


class TestEqualityContains:
    def test_course_eq_course(self):
        assert PORT / Fallback("a") / Item("b") / Call("c") == PORT / "a" / "b" / "c"

    def test_course_ne_course(self):
        assert PORT / Fallback("a") / Item("b") / Call("c") != PORT / "a" / "b()" / "c"

    def test_course_eq_str(self):
        assert Course("a", "b", "c", "d") == "a/b/c/d"

    def test_contains(self, course_basic):
        assert Fallback("a") in course_basic
        assert Fallback("b") in course_basic
        assert Fallback("c") in course_basic
        assert Fallback("d") in course_basic
        assert Item("a") in course_basic
        assert Attr("a") in course_basic
        assert Call("a") in course_basic

        assert Fallback("e") not in course_basic

    def test_contains_types(self, course_types):
        assert Fallback("a") in course_types
        assert Attr("b") in course_types
        assert Item("c") in course_types
        assert Call("d") in course_types

        assert Fallback("b") in course_types
        assert Fallback("c") in course_types
        assert Fallback("d") in course_types

        assert Item("b") not in course_types
        assert Attr("c") not in course_types
        assert Item("d") not in course_types

    def test_contains_slice(self, course_basic):
        assert Course("a", "b") in course_basic
        assert Course("b", "c") in course_basic
        assert Course("c", "d") in course_basic
        assert Course("b", "c", "d") in course_basic
        assert Course("a", "b", "c", "d") in course_basic

        assert Course("a", "c") not in course_basic
        assert Course("d", "e") not in course_basic

    def test_ends_with(self, course_basic):
        end_course = Course("c", "d")
        end_course_single = Course("d")

        assert course_basic.ends_with(Fallback("d"))
        assert course_basic.ends_with(end_course)
        assert course_basic.ends_with(end_course_single)

    def test_ends_with_types(self, course_types):
        end_course = Course(Item("c"), Call("d"))
        end_course_single = Course(Call("d"))

        assert course_types.ends_with(Fallback("d"))
        assert course_types.ends_with(end_course)
        assert course_types.ends_with(end_course_single)

    def test_not_ends_with_values(self, course_basic):
        end_course = Course("b", "c")
        end_course_single = Course("e")

        assert not course_basic.ends_with(Fallback("e"))
        assert not course_basic.ends_with(end_course)
        assert not course_basic.ends_with(end_course_single)

    def test_not_ends_with_types(self, course_types):
        end_course = Course(Item("c"), Item("d"))
        end_course_single = Course(Item("d"))

        assert not course_types.ends_with(Item("d"))
        assert not course_types.ends_with(end_course)
        assert not course_types.ends_with(end_course_single)

    def test_starts_with(self, course_basic):
        start_course = Course("a", "b")
        start_course_single = Course("a")

        assert course_basic.starts_with(Fallback("a"))
        assert course_basic.starts_with(start_course)
        assert course_basic.starts_with(start_course_single)

    def test_starts_with_types(self):
        course_types = Course(Item("a"), Attr("b"), Item("c"), Call("d"))

        start_course = Course(Item("a"), Attr("b"))
        start_course_single = Course(Item("a"))

        assert course_types.starts_with(Item("a"))
        assert course_types.starts_with(start_course)
        assert course_types.starts_with(start_course_single)

    def test_parent(self, course_basic):
        assert course_basic.parent == Course("a", "b", "c")

    def test_end_point(self, course_basic):
        assert course_basic.end_point == Fallback("d")


class TestOperations:
    def test_fetch(self, data_structure_1):
        course = PORT / "list_data" / -1 / "two dict"
        assert course.fetch(data_structure_1) == 2

    def test_fetch_keyword(self, data_structure_1):
        course = PORT / "list_data" / -1 / "two dict"
        assert course.fetch(target=data_structure_1) == 2

    def test_fetch_default(self, data_structure_1):
        course = PORT / "list_data" / -1 / "three dict"

        with pytest.raises(NullNameError):
            course.fetch(data_structure_1)

        assert course.fetch(data_structure_1, default=3) == 3

    def test_place(self, data_structure_1):
        course = PORT / "list_data" / -1 / "two dict"
        course.place(data_structure_1, "changed value")
        assert data_structure_1.list_data[-1]["two dict"] == "changed value"

    def test_place_raises(self, data_structure_1):
        with pytest.raises(NullNameError):
            course = PORT / "list_data" / 100 / "two dict"
            course.place(data_structure_1, "changed value")

    def test_place_len_1(self):
        course = PORT / "one"
        target = dict()
        course.place(target, 1)
        assert target["one"] == 1

    def test_place_default_factory_list_in_dict(self):

        data = {"a": {}}

        course = PORT / "a" / Item("list", factory=list) / 0
        course.place(data, "value")

        assert data == {"a": {"list": ["value"]}}

    def test_place_default_factory_data_class_optional_list(self):
        @dataclass
        class TestData:
            data_list: Optional[list] = None

        data = TestData()

        course = PORT / Attr("data_list", factory=list) / "append()"
        course.place(data, "value")

        assert data == TestData(["value"])

    def test_place_factory_does_not_replace_existing(self):
        data = {"nested": ["zero", "one", "two"]}
        course = PORT / "nested" / Item(0, factory=list)
        course.place(data, "yay!")

        assert data == {"nested": ["yay!", "one", "two"]}
