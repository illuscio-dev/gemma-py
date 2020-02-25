import pytest
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional

from gemma import (
    Surveyor,
    Cartographer,
    Coordinate,
    Course,
    PORT,
    NullNameError,
    SuppressedErrors,
    NonNavigableError,
    Compass,
    NO_DEFAULT,
)


class TestBasicMapping:
    def test_dataclass_to_dict(
        self,
        data_simple,
        surveyor_generic: Surveyor,
        cartographer_generic: Cartographer,
    ):
        destination = dict()
        cartographer_generic.map(data_simple, destination, surveyor=surveyor_generic)

        assert destination == {"a": "a data", "b": "b data", "one": 1, "two": 2}

    def test_dataclass_to_dict_with_coords(
        self, data_simple, cartographer_generic: Cartographer
    ):

        root = Course()

        coordinates = [
            Coordinate(root / "a", root / "strings" / "a-mapped"),
            Coordinate(root / "b", root / "strings" / "b-mapped"),
            Coordinate(root / "one", root / "ints" / "one-mapped"),
            Coordinate(root / "two", root / "ints" / "two-mapped"),
        ]

        destination = defaultdict(dict)

        cartographer_generic.map(data_simple, destination, coordinates)

        assert destination == {
            "strings": {"a-mapped": "a data", "b-mapped": "b data"},
            "ints": {"one-mapped": 1, "two-mapped": 2},
        }

    def test_dataclass_to_dict_with_coords_and_default(
        self, data_simple, cartographer_generic: Cartographer
    ):

        root = Course()

        coordinates = [
            Coordinate(root / "a", root / "strings" / "a-mapped"),
            Coordinate(root / "b", root / "strings" / "b-mapped"),
            Coordinate(root / "one", root / "ints" / "one-mapped"),
            Coordinate(root / "two", root / "ints" / "two-mapped"),
            Coordinate(root / "seven", root / "ints" / "seven-mapped", default=7),
        ]

        destination = defaultdict(dict)

        cartographer_generic.map(data_simple, destination, coordinates)

        assert destination == {
            "strings": {"a-mapped": "a data", "b-mapped": "b data"},
            "ints": {"one-mapped": 1, "two-mapped": 2, "seven-mapped": 7},
        }

    def test_dataclass_to_dict_with_coords_and_surveyor(
        self,
        data_simple,
        cartographer_generic: Cartographer,
        surveyor_generic: Surveyor,
    ):

        root = Course()

        coordinates = [
            Coordinate(root / "a", root / "strings" / "a-mapped"),
            Coordinate(root / "one", root / "ints" / "one-mapped"),
            Coordinate(root / "two", root / "ints" / "two-mapped"),
        ]

        destination = defaultdict(defaultdict)

        cartographer_generic.map(
            data_simple, destination, coordinates, surveyor=surveyor_generic
        )

        assert destination == {
            "strings": {"a-mapped": "a data"},
            "ints": {"one-mapped": 1, "two-mapped": 2},
            "b": "b data",
        }

    def test_dict_to_dataclass_ignore_missing(
        self,
        data_simple,
        surveyor_generic: Surveyor,
        cartographer_generic: Cartographer,
    ):

        origin_dict = {"a": "a new", "b": "b new", "c": "c new", "one": 11, "two": 22}

        try:
            cartographer_generic.map(
                origin_dict, data_simple, surveyor=surveyor_generic, exceptions=False
            )
        except SuppressedErrors:
            pass

        assert data_simple.a == "a new"
        assert data_simple.b == "b new"
        assert data_simple.one == 11
        assert data_simple.two == 22

        with pytest.raises(AttributeError):
            assert data_simple.c == "c new"

    def test_reuse_coords(self, data_simple, cartographer_generic: Cartographer):

        coords = [
            Coordinate(PORT / "a"),
            Coordinate(PORT / "b"),
            Coordinate(PORT / "one"),
            Coordinate(PORT / "two"),
        ]

        origin_list = [
            {"a": "a new1", "b": "b new1", "one": 1, "two": 2},
            {"a": "a new2", "b": "b new2", "one": 2, "two": 3},
        ]

        for i, this_origin in enumerate(origin_list, start=1):

            cartographer_generic.map(
                origin_root=this_origin, dst_root=data_simple, coordinates=coords
            )

            assert data_simple.a == f"a new{i}"
            assert data_simple.b == f"b new{i}"
            assert data_simple.one == i
            assert data_simple.two == i + 1


class TestCleanerFunctions:
    def test_dataclass_to_dict_origin_transform(
        self, data_simple, surveyor_generic: Surveyor
    ):
        class NewCart(Cartographer):
            def clean_org(self, course, coordinate: Coordinate) -> Course:
                end_point = course.end_point
                end_point = type(end_point)(end_point.name.replace("-extra", ""))
                return course.with_end_point(end_point)

        root = Course()

        coordinates = [
            Coordinate(root / "a-extra"),
            Coordinate(root / "b-extra"),
            Coordinate(root / "one-extra"),
            Coordinate(root / "two-extra"),
        ]

        destination = dict()
        cartographer = NewCart()

        cartographer.map(
            data_simple, destination, coordinates, surveyor=surveyor_generic
        )

        assert destination == {"a": "a data", "b": "b data", "one": 1, "two": 2}

    def test_dataclass_to_dict_destination_transform(
        self, data_simple, surveyor_generic: Surveyor
    ):
        class NewCart(Cartographer):
            def clean_dst(self, course: Course, coordinate: Coordinate) -> Course:
                course = super().clean_dst(course, coordinate)
                end_point = course.end_point.name + " changed"
                return course.with_end_point(end_point)

        destination = dict()
        cartographer = NewCart()

        cartographer.map(data_simple, destination, surveyor=surveyor_generic)

        assert destination == {
            "a changed": "a data",
            "b changed": "b data",
            "one changed": 1,
            "two changed": 2,
        }

    def test_dataclass_to_dict_value_transform(
        self,
        data_simple,
        surveyor_generic: Surveyor,
        cartographer_transform_value: Cartographer,
    ):

        root = Course()

        coordinates = [
            Coordinate(root / "a"),
            Coordinate(root / "b"),
            Coordinate(root / "one"),
            Coordinate(root / "two"),
        ]

        destination = dict()

        cartographer_transform_value.map(
            data_simple, destination, coordinates, surveyor=surveyor_generic
        )

        assert destination == {
            "a": "a data transformed",
            "b": "b data transformed",
            "one": "1 transformed",
            "two": "2 transformed",
        }

    def test_dataclass_to_dict_single_value_transform(
        self,
        data_simple,
        surveyor_generic: Surveyor,
        cartographer_generic: Cartographer,
    ):

        root = Course()

        def clean_b(value, coordinate: Coordinate, cache: dict) -> str:
            return value + " changed"

        coordinates = [Coordinate(root / "b", clean_value=clean_b)]
        destination = dict()

        cartographer_generic.map(
            data_simple, destination, coordinates, surveyor=surveyor_generic
        )

        assert destination == {"a": "a data", "b": "b data changed", "one": 1, "two": 2}

    def test_dataclass_to_dict_single_value_transform_with_default(
        self,
        data_simple,
        surveyor_generic: Surveyor,
        cartographer_transform_value: Cartographer,
    ):

        root = Course()

        def clean_b(value, coordinate: Coordinate, cache: dict) -> str:
            return value + " changed"

        coordinates = [Coordinate(root / "b", clean_value=clean_b)]
        destination = dict()
        cartographer_transform_value.map(
            data_simple, destination, coordinates, surveyor=surveyor_generic
        )

        assert destination == {
            "a": "a data transformed",
            "b": "b data changed",
            "one": "1 transformed",
            "two": "2 transformed",
        }

    def test_clean_origin_one_off(
        self,
        data_simple,
        surveyor_generic: Surveyor,
        cartographer_generic: Cartographer,
    ):
        def clean_a_orig(course, coordinate: Coordinate, cache: dict) -> Course:
            return course.with_end_point("a")

        root = Course()

        coordinates = [Coordinate(root / "a-extra", clean_org=clean_a_orig)]

        destination = dict()

        cartographer_generic.map(
            data_simple, destination, coordinates, surveyor=surveyor_generic
        )

        assert destination == {"a": "a data", "b": "b data", "one": 1, "two": 2}

    def test_clean_dst_one_off(
        self,
        data_simple,
        surveyor_generic: Surveyor,
        cartographer_generic: Cartographer,
    ):
        def clean_b_dst(course, coordinate: Coordinate, cache: dict) -> Course:
            return coordinate.org.with_end_point("b-extra")

        root = Course()

        coordinates = [Coordinate(root / "b", clean_dst=clean_b_dst)]

        destination = dict()

        cartographer_generic.map(
            data_simple, destination, coordinates, surveyor=surveyor_generic
        )

        assert destination == {"a": "a data", "b-extra": "b data", "one": 1, "two": 2}


class TestManyToMany:
    def test_dict_to_dict_one_to_many(
        self, cartographer_generic: Cartographer, surveyor_generic: Surveyor
    ):

        origin = {"id": 200, "name": ["Peake", "William", None, "III"]}
        dst = defaultdict(dict)

        name_part_lookup = ["last", "first", "middle", "suffix"]

        def extract_name(value, coordinate: Coordinate, cache: dict):
            name_part = coordinate.dst.end_point.name
            part_index = name_part_lookup.index(name_part)
            return value[part_index]

        root = Course()

        coordinates = [
            Coordinate(
                root / "name", root / "name" / "first", clean_value=extract_name
            ),
            Coordinate(root / "name", root / "name" / "last", clean_value=extract_name),
            Coordinate(
                root / "name", root / "name" / "middle", clean_value=extract_name
            ),
            Coordinate(
                root / "name", root / "name" / "suffix", clean_value=extract_name
            ),
        ]

        cartographer_generic.map(origin, dst, coordinates, surveyor=surveyor_generic)

        assert dst == {
            "id": 200,
            "name": {
                "first": "William",
                "last": "Peake",
                "middle": None,
                "suffix": "III",
            },
        }

    def test_dict_to_dict_one_to_many_using_cache(
        self, cartographer_generic: Cartographer, surveyor_generic: Surveyor
    ):

        origin = {"id": 200, "name": "William Peake III"}
        dst = defaultdict(dict)

        def extract_name(value, coordinate: Coordinate, cache: dict):
            name_parts = value.split(" ")

            cache["name.first"] = name_parts[0]
            cache["name.last"] = name_parts[1]
            cache["name.middle"] = None
            cache["name.suffix"] = name_parts[-1]

            name_part = coordinate.clean.dst_list[0].end_point.name
            return cache[f"name.{name_part}"]

        def get_cached(value, coordinate: Coordinate, cache: dict):
            name_part = coordinate.dst.end_point.name
            return cache[f"name.{name_part}"]

        root = Course()

        coordinates = [
            Coordinate(
                root / "name", root / "name" / "first", clean_value=extract_name
            ),
            Coordinate(root / "name", root / "name" / "last", clean_value=get_cached),
            Coordinate(root / "name", root / "name" / "middle", clean_value=get_cached),
            Coordinate(root / "name", root / "name" / "suffix", clean_value=get_cached),
        ]

        cartographer_generic.map(origin, dst, coordinates, surveyor=surveyor_generic)

        assert dst == {
            "id": 200,
            "name": {
                "first": "William",
                "last": "Peake",
                "middle": None,
                "suffix": "III",
            },
        }

    def test_many_to_one_coord(self, cartographer_generic, photo_info):
        def marry_dimensions(value, coord: Coordinate, cache: dict) -> str:
            return f"{value[0]}x{value[1]}"

        destination = dict()

        coords = [
            Coordinate(
                org=(PORT / "width", PORT / "height"),
                dst=PORT / "dimensions",
                clean_value=marry_dimensions,
            )
        ]
        cartographer_generic.map(photo_info, destination, coords)

        assert destination == {"dimensions": "1920x1080"}

    def test_many_to_one_coord_defaults(self, cartographer_generic):
        def marry_dimensions(value, coord: Coordinate, cache: dict) -> str:
            return f"{value[0]}x{value[1]}"

        destination = dict()

        coords = [
            Coordinate(
                org=(PORT / "width", PORT / "height"),
                dst=PORT / "dimensions",
                clean_value=marry_dimensions,
                default=(1280, 720),
            )
        ]
        cartographer_generic.map(dict(), destination, coords)

        assert destination == {"dimensions": "1280x720"}

    def test_many_to_one_coord_single_default(self, cartographer_generic):
        def marry_dimensions(value, coord: Coordinate, cache: dict) -> str:
            return f"{value[0]}x{value[1]}"

        source = {"height": 720}
        destination = dict()

        coords = [
            Coordinate(
                org=(PORT / "width", PORT / "height"),
                dst=PORT / "dimensions",
                clean_value=marry_dimensions,
                default=(1280, NO_DEFAULT),
            )
        ]
        cartographer_generic.map(source, destination, coords)

        assert destination == {"dimensions": "1280x720"}

    @pytest.mark.parametrize(
        "source,default",
        [({"width": 1920}, (1280, NO_DEFAULT)), ({"height": 1080}, (NO_DEFAULT, 720))],
    )
    def test_many_to_one_coord_single_default_raises(
        self, cartographer_generic, source, default
    ):
        def marry_dimensions(value, coord: Coordinate, cache: dict) -> str:
            return f"{value[0]}x{value[1]}"

        destination = dict()

        coords = [
            Coordinate(
                org=(PORT / "width", PORT / "height"),
                dst=PORT / "dimensions",
                clean_value=marry_dimensions,
                # We have a default for width here but not height, so this should throw
                # an error.
                default=default,
            )
        ]

        with pytest.raises(NullNameError):
            cartographer_generic.map(source, destination, coords)

    def test_non_matching_defaults_length_raises(self):
        with pytest.raises(ValueError):
            Coordinate(
                org=(PORT / "width", PORT / "height"),
                dst=PORT / "dimensions",
                # We have a default for width here but not height, so this should throw
                # an error.
                default=(1280,),
            )

    def test_one_to_many(self, cartographer_generic, photo_info):
        def split_dimensions(value, coord: Coordinate, cache: dict):
            split = value.split("x")
            return int(split[0]), int(split[1])

        destination = dict()

        coords = [
            Coordinate(
                org=PORT / "resolution",
                dst=(PORT / "x", PORT / "y"),
                clean_value=split_dimensions,
            )
        ]
        cartographer_generic.map(photo_info, destination, coords)

        assert destination == {"x": 1280, "y": 720}


class TestSuppressErrors:
    def test_raises_null_name_origin(self):

        data = {"a": "a value"}

        coords = [Coordinate(org=PORT / "b")]

        with pytest.raises(NullNameError):
            Cartographer().map(data, dict(), coords)

    def test_raises_null_name_destination(self):

        data = {"a": "a value", "b": "b value"}

        @dataclass
        class Dest:
            a: Optional[str] = None

        destination = Dest()

        coords = [Coordinate(org=PORT / "a"), Coordinate(org=PORT / "b")]

        with pytest.raises(NullNameError):
            Cartographer().map(data, destination, coords)

    def test_raises_null_name_destination_surveyor(self):

        data = {"a": "a value", "b": "b value"}

        @dataclass
        class Dest:
            a: Optional[str] = None

        destination = Dest()

        with pytest.raises(NullNameError):
            Cartographer().map(data, destination, surveyor=Surveyor())

    def test_raises_non_navigable(self):

        data = {"a": "a value", "list": [1, 2, 3]}

        comp = Compass(target_types=dict)
        survey = Surveyor(compasses=[comp])

        with pytest.raises(NonNavigableError):
            Cartographer().map(data, dict(), surveyor=survey)

    def test_raises_suppressed_null_name_source(self):

        data = {"a": "a value", "d": "d value"}

        coords = [
            Coordinate(org=PORT / "a"),
            Coordinate(org=PORT / "b"),
            Coordinate(org=PORT / "c"),
            Coordinate(org=PORT / "d"),
        ]

        destination = dict()
        raised = None

        with pytest.raises(SuppressedErrors):
            try:
                Cartographer().map(data, destination, coords, exceptions=False)
            except SuppressedErrors as error:
                raised = error
                raise error

        assert len(raised.errors) == 2
        assert isinstance(raised.errors[0], NullNameError)
        assert isinstance(raised.errors[1], NullNameError)

        assert destination == {"a": "a value", "d": "d value"}

    def test_raises_suppressed_null_name_destination(self):

        data = {"a": "a value", "b": "b value", "c": "c value"}

        @dataclass
        class Dest:
            b: Optional[str] = None

        destination = Dest()

        coords = [
            Coordinate(org=PORT / "a"),
            Coordinate(org=PORT / "b"),
            Coordinate(org=PORT / "c"),
        ]

        with pytest.raises(SuppressedErrors):
            try:
                Cartographer().map(data, destination, coords, exceptions=False)
            except SuppressedErrors as error:
                raised = error
                raise error

        assert len(raised.errors) == 2
        assert isinstance(raised.errors[0], NullNameError)
        assert isinstance(raised.errors[1], NullNameError)

        assert destination == Dest("b value")

    def test_raises_suppressed_non_navigable(self):

        data = {"a": "a value", "list1": [1, 2, 3], "list2": [4, 5, 6], "b": "b value"}
        destination = dict()

        comp = Compass(target_types=dict)
        survey = Surveyor(compasses=[comp])

        raised = None

        with pytest.raises(SuppressedErrors):
            try:
                Cartographer().map(data, destination, surveyor=survey, exceptions=False)
            except SuppressedErrors as error:
                raised = error
                raise error

        assert len(raised.errors) == 2
        assert isinstance(raised.errors[0], NonNavigableError)
        assert isinstance(raised.errors[1], NonNavigableError)

        assert destination == data

    def test_raises_suppressed_null_name_survey(self):

        data = {"a": "a value", "b": "b value"}

        @dataclass
        class Dest:
            a: Optional[str] = None

        destination = Dest()
        survey = Surveyor()

        raised = None

        with pytest.raises(SuppressedErrors):
            try:
                Cartographer().map(data, destination, surveyor=survey, exceptions=False)
            except SuppressedErrors as error:
                raised = error
                raise error

        assert len(raised.errors) == 1
        assert isinstance(raised.errors[0], NullNameError)

        assert destination == Dest("a value")
