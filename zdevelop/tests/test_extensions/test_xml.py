import pytest
from xml.etree.ElementTree import Element, SubElement
from typing import Tuple, Any, Union

from gemma import (
    bearing,
    Call,
    Attr,
    Item,
    Fallback,
    NullNameError,
    Course,
    BearingAbstract,
    Cartographer,
    Coordinate,
)
from gemma.extensions.xml import XElm, XCourse, XPATH, XCompass, xbearing, xsurveyor
from gemma.extensions.xml._xelm_bearing import _string_to_slice


@pytest.fixture
def element_tree() -> Element:
    root: Element = Element("root")
    sub_a: Element = SubElement(root, "a", {"1": 1, "2": 2})
    sub_a.text = "a value"

    sub_b: Element = SubElement(root, "b", {"3": 3, "4": 4})

    listed_one: Element = SubElement(sub_b, "listed")
    listed_two: Element = SubElement(sub_b, "listed")
    listed_three: Element = SubElement(sub_b, "listed")

    listed_one.text = "one"
    listed_two.text = "two"
    listed_three.text = "three"

    return root


@pytest.fixture
def element_list() -> Element:
    root: Element = Element("root")

    listed_zero: Element = SubElement(root, "listed")
    listed_one: Element = SubElement(root, "listed")
    listed_two: Element = SubElement(root, "listed")

    listed_zero.text = "zero"
    listed_one.text = "one"
    listed_two.text = "two"

    return root


@pytest.fixture
def single_element() -> Element:
    root = Element("a", {"1": 1, "2": 2})
    return root


@pytest.fixture
def bearing_list() -> list:
    return [XElm, Item, Call, Attr, Fallback]


@pytest.fixture()
def fallback_bearing(bearing_list):
    return bearing("a", bearing_list)


@pytest.mark.parametrize(
    "text,answer",
    [
        ("1:5", slice(1, 5)),
        ("1 :5", slice(1, 5)),
        ("1 : 5", slice(1, 5)),
        ("1:", slice(1, None)),
        ("1 :", slice(1, None)),
        ("1 : ", slice(1, None)),
        (":5", slice(None, 5)),
        (": 5", slice(None, 5)),
        (" : 5", slice(None, 5)),
        (" : 5 ", slice(None, 5)),
    ],
)
def test_cast_slice(text, answer):
    assert _string_to_slice(text) == answer


class TestBearing:
    @pytest.mark.parametrize(
        "name,index",
        [
            ("<name>", 0),
            ("<name,5>", 5),
            ("<name,1:5>", slice(1, 5)),
            ("< name , 5>", 5),
            ("< name ,5 >", 5),
            ("< name , 5 >", 5),
            ("<name,1 :5>", slice(1, 5)),
            ("<name,1 : 5>", slice(1, 5)),
            ("<name, 1 : 5>", slice(1, 5)),
            ("<name, 0:>", slice(0, None)),
            ("<name, :5>", slice(None, 5)),
            (("name", 5), 5),
            (("name", slice(1, 5)), slice(1, 5)),
        ],
    )
    def test_cast(self, bearing_list, name, index):
        cast = bearing(name, bearing_list)
        assert isinstance(cast, XElm)
        assert cast.tag == "name"
        assert cast.index == index

    def test_cast_fallback(self, bearing_list):
        cast = bearing("name", bearing_list)
        assert XElm in cast.BEARING_CLASSES

    def test_factory_type(self):
        cast = XElm("name", factory=Element)
        assert cast.factory_type == Element

    def test_factory_initialized_elm(self):
        cast = XElm("name", factory=Element)
        assert cast.init_factory().tag == "name"

    def test_factory_initialized_dict(self):
        cast = XElm("name", factory=dict)
        assert cast.init_factory() == dict()

    def test_cast_raises(self):
        with pytest.raises(TypeError):
            XElm(("name", float(5)))

    def test_factory_type_raises(self):
        cast = XElm("name")
        with pytest.raises(TypeError):
            assert cast.init_factory()

    def test_str(self):
        assert str(XElm("name")) == "<name, 0>"

    @pytest.mark.parametrize(
        "name,source,text",
        [("a", "element_tree", "a value"), (("listed", 1), "element_list", "one")],
    )
    def test_fetch(self, name, source, text, element_tree, element_list):
        if source == "element_tree":
            source = element_tree
        elif source == "element_list":
            source = element_list

        this_bearing = XElm(name)
        result = this_bearing.fetch(source)

        assert result.text == text

    @pytest.mark.parametrize(
        "this_slice,answer",
        [
            (slice(0, None), ["zero", "one", "two"]),
            (slice(1, None), ["one", "two"]),
            (slice(None, -1), ["zero", "one"]),
            (slice(1, 3), ["one", "two"]),
        ],
    )
    def test_fetch_slice(self, element_list, this_slice, answer):
        to_fetch = XElm(("listed", this_slice))
        fetched = to_fetch.fetch(element_list)
        assert [x.text for x in fetched] == answer

    def test_fetch_raises(self, element_list):
        with pytest.raises(NullNameError):
            this_bearing = XElm("d")
            this_bearing.fetch(element_list)

    def test_place_element(self, element_tree: Element):
        this_bearing = XElm("b")
        this_bearing.place(element_tree, Element("sub_b", {"key": "value"}))

        assert element_tree.find("b").find("sub_b").attrib["key"] == "value"

    def test_fallback_fetch(self, element_tree, fallback_bearing):
        this_bearing = fallback_bearing.fetch(element_tree)
        assert this_bearing.text == "a value"

    def test_fallback_place(self, element_tree, fallback_bearing):
        value = Element("changed")
        fallback_bearing.place(element_tree, value)
        assert element_tree.find("a").find("changed") == value

    @pytest.mark.parametrize(
        "name, answer",
        [("<name>", XElm(("name", 0))), ("<name, 5>", XElm(("name", 5)))],
    )
    def test_xbearing_factory_str(self, name, answer):
        assert xbearing(name) == answer


class TestCourse:
    def test_cast_str(self):
        course = XPATH / "<a>"
        assert course[0].name == ("a", 0)
        assert isinstance(course[0], XElm)

    def test_cast_tuple(self):
        course = XPATH / ("a", 0)
        assert course[0].name == ("a", 0)
        assert isinstance(course[0], XElm)

    @pytest.mark.parametrize(
        "course,answer",
        [
            (XPATH / XElm("a") / "text", "a value"),
            (XPATH / "<a>" / "text", "a value"),
            (XPATH / "<a>" / "attrib" / "1", 1),
            (XPATH / "<b>" / "attrib" / "3", 3),
            (XPATH / XElm("b") / XElm(("listed", 0)) / "text", "one"),
            (XPATH / "<b>" / "<listed, 0>" / "text", "one"),
            (XPATH / XElm("b") / XElm(("listed", 1)) / "text", "two"),
            (XPATH / XElm("b") / "<listed, 1>" / "text", "two"),
            (XPATH / XElm("b") / XElm(("listed", 2)) / "text", "three"),
            (XPATH / XElm("b") / "<listed, 2>" / "text", "three"),
            (XPATH / XElm("b") / XElm(("listed", -1)) / "text", "three"),
            (XPATH / XElm("b") / "<listed, -1>" / "text", "three"),
        ],
    )
    def test_course_fetch(self, element_tree, course, answer):
        value = course.fetch(element_tree)
        assert value == answer

    @pytest.mark.parametrize(
        "course",
        [
            XCourse() / XElm("c"),
            XCourse() / XElm("c"),
            XCourse() / XElm("b") / XElm(("listed", 5)),
            XCourse() / XElm("b") / XElm(("listed", -5)),
        ],
    )
    def test_course_fetch_raises(self, element_tree, course):
        with pytest.raises(NullNameError):
            course.fetch(element_tree)

    @pytest.mark.parametrize(
        "course,value",
        [
            (XCourse() / XElm("a") / "text", "new value"),
            (XCourse() / XElm("a") / "attrib" / "new", "new value"),
            (XCourse() / XElm("b") / XElm(("listed", 0)) / "text", "new value"),
        ],
    )
    def test_course_place(self, course, value, element_tree):
        course.place(element_tree, value)
        assert course.fetch(element_tree) == value

    def test_course_place_element(self, element_tree):
        to_place = Element("new")

        course = XPATH / "<b, -1>"
        course.place(element_tree, to_place)

        assert element_tree.find("b").find("new") is to_place

    def test_course_place_element_factory(self, element_tree):
        course = XPATH / "b" / XElm("new_route", factory=Element) / "text"
        course.place(element_tree, "new value")
        assert element_tree.find("b").find("new_route").text == "new value"

    @pytest.mark.parametrize(
        "course, value",
        [
            (XPATH / XElm("c") / "text", 0),
            (XPATH / XElm("c"), Element("name")),
            (XPATH / XElm("b") / XElm(("listed", 5)) / "text", 0),
            (XPATH / XElm("b") / XElm(("listed", 5)), Element("name")),
        ],
    )
    def test_course_place_raises(self, element_tree, course, value):
        with pytest.raises(NullNameError):
            course.place(element_tree, value)


EqPairType = Tuple[Union[BearingAbstract, Course], Any]


def bearing_value_eq(pair1: EqPairType, pair2: EqPairType) -> bool:

    if not isinstance(pair1[1], Element) or not isinstance(pair2[1], Element):
        return pair1 == pair2
    else:
        print("test1")
        if pair1[0] != pair2[0]:
            return False

        elm1: Element = pair1[1]
        elm2: Element = pair2[1]

        if elm1.tag != elm2.tag:
            return False
        elif elm1.text != elm2.text:
            return False
        elif elm1.attrib != elm2.attrib:
            return False
        else:
            return True


class TestCompass:
    def test_map_routes(self, element_tree):
        a_element = Element("a", attrib={"1": 1, "2": 2})
        a_element.text = "a value"

        answer = [
            (Attr("text"), None),
            (Attr("attrib"), dict()),
            (XElm(("a", 0)), a_element),
            (XElm(("b", 0)), Element("b", attrib={"3": 3, "4": 4})),
        ]

        result = XCompass().bearings(element_tree)

        for pair1, pair2 in zip(result, answer):
            assert bearing_value_eq(pair1, pair2)

    def test_map_elms_false(self, element_tree):
        compass = XCompass(elms=False)
        answer = [(Attr("text"), None), (Attr("attrib"), dict())]
        assert compass.bearings(element_tree) == answer

    def test_map_elms_restricted(self, element_tree):
        compass = XCompass(elms=["b"])
        answer = [
            (Attr("text"), None),
            (Attr("attrib"), dict()),
            (XElm(("b", 0)), Element("b", attrib={"3": 3, "4": 4})),
        ]
        result = compass.bearings(element_tree)

        for pair1, pair2 in zip(result, answer):
            assert bearing_value_eq(pair1, pair2)


def test_xsurveyor(element_tree):

    sub_a: Element = Element("a", {"1": 1, "2": 2})
    sub_a.text = "a value"

    sub_b: Element = Element("b", {"3": 3, "4": 4})

    listed_one: Element = SubElement(sub_b, "listed")
    listed_two: Element = SubElement(sub_b, "listed")
    listed_three: Element = SubElement(sub_b, "listed")

    listed_one.text = "one"
    listed_two.text = "two"
    listed_three.text = "three"

    answer = [
        (XPATH / "text", None),
        (XPATH / "attrib", dict()),
        (XPATH / "<a>", sub_a),
        (XPATH / "<a>" / "text", "a value"),
        (XPATH / "<a>" / "attrib", {"1": 1, "2": 2}),
        (XPATH / "<a>" / "attrib" / "1", 1),
        (XPATH / "<a>" / "attrib" / "2", 2),
        (XPATH / "<b>", sub_b),
        (XPATH / "<b>" / "text", None),
        (XPATH / "<b>" / "attrib", {"3": 3, "4": 4}),
        (XPATH / "<b>" / "attrib" / "3", 3),
        (XPATH / "<b>" / "attrib" / "4", 4),
        (XPATH / "<b>" / "<listed, 0>", listed_one),
        (XPATH / "<b>" / "<listed, 0>" / "text", "one"),
        (XPATH / "<b>" / "<listed, 0>" / "attrib", dict()),
        (XPATH / "<b>" / "<listed, 1>", listed_two),
        (XPATH / "<b>" / "<listed, 1>" / "text", "two"),
        (XPATH / "<b>" / "<listed, 1>" / "attrib", dict()),
        (XPATH / "<b>" / "<listed, 2>", listed_three),
        (XPATH / "<b>" / "<listed, 2>" / "text", "three"),
        (XPATH / "<b>" / "<listed, 2>" / "attrib", dict()),
    ]

    for pair1, pair2 in zip(xsurveyor.chart_iter(element_tree), answer):
        print(pair1, pair2)
        assert bearing_value_eq(pair1, pair2)


def test_cartographer(element_tree):
    cart = Cartographer()

    def explode_listed(listed_elements, coord, cache):
        return [x.text for x in listed_elements]

    coords = [
        Coordinate(org=XPATH / "a" / "text", dst=XPATH / "a.tag"),
        Coordinate(org=XPATH / "a" / "attrib" / "1", dst=XPATH / "a.one"),
        Coordinate(org=XPATH / "a" / "attrib" / "2", dst=XPATH / "a.two"),
        Coordinate(org=XPATH / "b" / "attrib" / "3", dst=XPATH / "b.three"),
        Coordinate(org=XPATH / "b" / "attrib" / "4", dst=XPATH / "b.four"),
        Coordinate(
            org=XPATH / "b" / "<listed, 0:>",
            dst=XPATH / "b.listed",
            clean_value=explode_listed,
        ),
    ]

    answer = {
        "a.tag": "a value",
        "a.one": 1,
        "a.two": 2,
        "b.three": 3,
        "b.four": 4,
        "b.listed": ["one", "two", "three"],
    }

    destination = dict()
    cart.map(element_tree, destination, coords)

    assert destination == answer
