import itertools
from typing import (
    Tuple,
    Any,
    Union,
    Generator,
    Iterator,
    overload,
    List,
    Type,
    Iterable,
)

from ._bearings import BearingAbstract, Fallback, bearing, _BEARING_CLASSES
from ._exceptions import NullNameError
from ._flags import NO_DEFAULT


class Course:
    BEARINGS: List[Type[BearingAbstract]] = _BEARING_CLASSES + [Fallback]
    BEARINGS_EXTENSION: List[Type[BearingAbstract]] = list()

    def __init__(self, *bearings: Union[Tuple["CourseInput", ...], "CourseInput"]):
        """
        Sequence of bearings that lead to data in a structure.

        :param bearings: :class:`Bearing` or :class:`Course` objects to be combined into
            new course.

        The core functionality of a course are its :func:`Course.fetch` and
        :func:`Course.place` methods. See their documentation below.
        """
        args: Iterator[BearingAbstract] = (x for x in self._cast_init(bearings))
        self._bearings: Tuple[BearingAbstract, ...] = tuple(args)

    def __repr__(self) -> str:
        return f"<Course: {' / '.join(repr(x) for x in self)}>"

    def __str__(self) -> str:
        return "/".join(str(x) for x in self._bearings)

    def __len__(self) -> int:
        return len(self._bearings)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Course):
            other = Course(other)
        return other._bearings == self._bearings

    # flake8 does not understand overloads, noqa comments are to ignore re-definition
    # errors during lint
    @overload  # noqa: F811
    def __getitem__(self, item: int) -> BearingAbstract:
        ...

    @overload
    def __getitem__(self, item: slice) -> "Course":  # noqa: F811
        ...

    def __getitem__(  # noqa: F811
        self, item: Union[int, slice]
    ) -> Union[BearingAbstract, "Course"]:
        if isinstance(item, slice):
            return type(self)(*self._bearings[item])
        else:
            return self._bearings[item]

    def __iter__(self) -> Generator[BearingAbstract, None, None]:
        for this_bearing in self._bearings:
            yield this_bearing

    def __truediv__(self, other: "CourseInput") -> "Course":
        return type(self)(self, other)

    def __contains__(self, item: Union[BearingAbstract, "Course"]) -> bool:
        item = type(self)(item)
        slices = zip(range(0, len(self) - len(item) + 1), itertools.count(len(item)))

        for x, y in slices:
            if type(self)(*self[x:y]) == item:
                return True

        return False

    @property
    def parent(self) -> "Course":
        """
        Parent course of current course

        :return: parent

        >>> from gemma import Course
        >>> example = Course() / "one" / "two" / "three"
        >>> example
        <Course: <Fallback: 'one'> / <Fallback: 'two'> / <Fallback: 'three'>>
        >>> example.parent
        <Course: <Fallback: 'one'> / <Fallback: 'two'>>
        """
        return Course(*self._bearings[:-1])

    @property
    def end_point(self) -> BearingAbstract:
        """
        Last bearing of current course

        :return: end point of course

        >>> from gemma import Course
        >>> example = Course() / "one" / "two" / "three"
        >>> example
        <Course: <Fallback: 'one'> / <Fallback: 'two'> / <Fallback: 'three'>>
        >>> example.end_point
        <Fallback: 'three'>
        """
        return self._bearings[-1]

    def with_end_point(self, end_point: "CourseInput") -> "Course":
        """
        Returns course with new end point.

        :param end_point: bearing to use as new end point.
        :return: New Course.

        >>> from gemma import Course
        >>> example = Course() / "one" / "two" / "three"
        >>> example
        <Course: <Fallback: 'one'> / <Fallback: 'two'> / <Fallback: 'three'>>
        >>> example.with_end_point("new")
        <Course: <Fallback: 'one'> / <Fallback: 'two'> / <Fallback: 'new'>>
        """
        return Course(self.parent, end_point)

    def starts_with(self, other: Union[BearingAbstract, "Course"]) -> bool:
        """
        Checks if course starts with ``other`` :class:`Bearing` or :class:`Course`.

        :param other: Bearing or Sub-Course to check
        :return: True: Course starts with ``other``

        >>> from gemma import Course, Fallback
        >>>
        >>> example = Course() / "one" / "two" / "three" / "four"
        >>> head = Course() / "one" / "two"
        >>> middle = Course() / "two" / "three"
        >>>
        >>> example.starts_with(Fallback("one"))
        True
        >>> example.starts_with(Fallback("two"))
        False
        >>>
        >>> example.starts_with(head)
        True
        >>> example.starts_with(middle)
        False

        For more detail, see the :ref:`contains` section below.
        """
        if isinstance(other, BearingAbstract):
            return self[0] == other
        else:
            return self[: len(other)] == other

    def ends_with(self, other: Union[BearingAbstract, "Course"]) -> bool:
        """
        Checks if course ends with ``other`` :class:`Bearing` or :class:`Course`.

        :param other: Bearing or Sub-Course to check
        :return: True: Course ends with ``other``

        >>> from gemma import Course(), Fallback
        >>>
        >>> example = Course() / "one" / "two" / "three" / "four"
        >>> tail = Course() / "three" / "four"
        >>> middle = Course() / "two" / "three"
        >>>
        >>> example.ends_with(Fallback("four"))
        True
        >>> example.ends_with(Fallback("three"))
        False
        >>>
        >>> example.ends_with(tail)
        True
        >>> example.ends_with(middle)
        False

        For more detail, see the :ref:`contains` section below.
        """
        if isinstance(other, BearingAbstract):
            return self[-1] == other
        else:
            start = -len(other)
            return self[start:] == other

    def replace(self, index: Union[int, slice], replacement: "CourseInput") -> "Course":
        """
        Replace bearings at index / slice with ``replacement``

        :param index: item(s) to replace
        :param replacement: Replacement bearing / course
        :return:

        >>> course = PORT / "thing" / 10 / "key"
        >>> course.replace(1, 11)
        <Course: <Fallback: 'thing'> / <Item: 11> / <Fallback: 'key'>>

        >>> course.replace(slice(1, 3), 14)
        <Course: <Fallback: 'thing'> / <Item: 14> / <Fallback: 'sub-key'>>

        >>> course.replace(slice(1, 3), PORT / 14 / "key2")
        <Course: <Fallback: 'thing'> / <Item: 14> / <Fallback: 'key2'> / ...>>
        """
        bearing_list: List["CourseInput"] = list(self._bearings)
        del bearing_list[index]

        start = index if isinstance(index, int) else index.start
        if start is None:
            start = 0
        else:
            start = start % len(self)
        bearing_list.insert(start, replacement)

        return Course(*bearing_list)

    def fetch(self, target: Any, *, default: Any = NO_DEFAULT) -> Any:  # noqa: F811
        """
        Traverses ``target``, getting data at end point of course.

        :param target: data structure to get data from.
        :param default: Optional parameter to pass default value. When passed this value
            will be used if the course does not exist on ``target``.
        :return: Value at end of course.
        :raises NullNameError: if any bearing cannot be found in ``target``

        Data is fetched by iterating through a course, running each bearing's
        :func:`BearingAbstract.fetch` method on the previously fetched object.

        Lets use the :ref:`data_dict` object from :func:`test_objects`
        as an example.

            >>> from gemma import Course(), Attr
            >>> from gemma.test_objects import test_objects
            >>>
            >>> simple, data_dict, data_list, structured, target = test_objects()
            >>> example_course = Course() / "[nested]" / "[one key]"
            >>>
            >>> example_course.fetch(data_dict)
            1

        What is happening in the example above? This course contains two
        :class:`Item` bearings. The :func:`Item.fetch` method gets a key
        or index. When the course executes a fetch, it first fetches the ``"nested"``
        key from the ``data_dict`` object. This returns a sub_dictionary with the
        data: ``{"one key": 1, "two key": 2}``

        The next bearing's fetch method is called on ``"one key"`` of the sub-dict,
        returning ``1``. This is the end of the course, so ``1`` is returned as the
        final value of the fetch.

        Each fetch down the chain follows the rules established in :ref:`Bearings`.

        If a bearing cannot be found at any point in the chain, :class:`NullNameError`
        is raised.

            >>> bad_course = Course() / "[non_existent]" / "[one key]"
            >>> bad_course.fetch(data_dict)
            Traceback (most recent call last):
                ...
            gemma._exceptions.NullNameError: [non_existent]

        We can supply a default value for non-existent targets like so:

            >>> bad_course.fetch(data_dict, default="default value fetched!")
            default value fetched!

        """
        for this_bearing in self:

            try:
                target = this_bearing.fetch(target)
            except NullNameError as error:
                if default is not NO_DEFAULT:
                    return default
                else:
                    raise error

        return target

    def place(self, target: Any, value: Any) -> None:
        """
        Traverses ``target`` to place data at :func:`Course.end_point`.

        :param target: data structure to place data on.
        :param value: value to place.
        :return: None. Changes are made in-place.
        :raises NullNameError: if any bearing cannot be found in ``target``

        :func:`Course.fetch` is called on the acting course's :func:`Course.parent`,
        returning the object that needs to be modified.

        :func:`BearingAbstract.place` of :func:`Course.end_point` is called on the
        object to place ``value``.

        Lets look at an example using the :ref:`target` object from
        :func:`test_objects`.

        >>> from gemma import Course
        >>> from gemma.test_objects import test_objects
        >>>
        >>> simple, data_dict, data_list, structured, target = test_objects()
        >>>
        >>> example_course = Course() / "dict_target" / "new key"
        >>>
        >>> example_course.place(target, 1)
        >>> target.dict_target["new key"]
        1

        See examples from the :class:`Course.fetch` method in the documentation below.
        :class:`Course.place` abides by the same rules, except final bearing, which uses
        :func:`BearingAbstract.place` instead of :func:`BearingAbstract.fetch`, and
        always returns ``None``
        """
        for this_bearing, i in zip(self.parent, itertools.count()):
            try:
                new_target = this_bearing.fetch(target)
            except NullNameError as error:
                if this_bearing.factory_type is None:
                    raise error
                new_target = None

            # if we have a type factory, we generate the node, and place it where it
            # should go on the current target
            factory = this_bearing.factory_type
            if factory is not None and not isinstance(new_target, factory):
                new_node: Any = this_bearing.init_factory()
                # some implementation may want to know that we are calling this as the
                #   factory version of the method
                kwargs: dict = {"place_factory": True}
                this_bearing.place(target, new_node, **kwargs)
                new_target = new_node

            target = new_target

        self.end_point.place(target, value)

    @classmethod
    def _cast_arg(cls, new: "CourseInput") -> Generator[BearingAbstract, None, None]:
        to_cast: Iterable["CourseInput"]

        if isinstance(new, Course):
            to_cast = (x for x in new)
        elif isinstance(new, str):
            to_cast = new.split("/")
        else:
            to_cast = [new]

        bearing_classes = cls.BEARINGS_EXTENSION + cls.BEARINGS
        for value in to_cast:
            if isinstance(value, BearingAbstract):
                yield value
            else:
                yield bearing(value, bearing_classes=bearing_classes)

    @classmethod
    def _cast_init(
        cls, args: Tuple["CourseInput", ...]
    ) -> Generator[BearingAbstract, None, None]:
        for arg in args:
            for this_bearing in cls._cast_arg(arg):
                yield this_bearing


CourseInput = Union[Course, BearingAbstract, str, Any]


PORT = Course()
