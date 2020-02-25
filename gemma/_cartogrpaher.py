import itertools

from ._surveyor import Surveyor
from ._course import Course
from ._bearings import Fallback
from ._exceptions import NullNameError, SuppressedErrors, NonNavigableError
from ._flags import NO_DEFAULT

from typing import Any, Callable, Optional, Iterable, List, Union, Tuple, Type
from dataclasses import dataclass, field, InitVar


@dataclass(frozen=True)
class Coordinate:
    org: Union[Course, Tuple[Course, ...]]
    """Origin course(s)"""
    dst: Optional[Union[Course, Tuple[Course, ...]]] = None
    """Destination course(s)"""
    clean_org: Optional[Callable] = None
    """Callable to clean origin course(s) path."""
    clean_dst: Optional[Callable] = None
    """Callable to clean destination course(s) path."""
    clean_value: Optional[Callable] = None
    """Callable to clean value(s) before they are set."""
    default: Union[Any, Tuple[Any, ...]] = NO_DEFAULT
    """
    Default value. If Coordinate.NO_DEFAULT, NullNameError will be thrown. Can use
    Coordinate.NO_DEFAULT or Tuple of source defaults.
    """
    clean: "CleanData" = field(init=False)

    def __post_init__(self) -> None:
        self._validate_default_length()

    def _validate_default_length(self) -> None:
        # If NO_DEFAULT we can return, as that means no matter what the origin courses
        # setup, none of them have defaults.
        if self.default is NO_DEFAULT:
            return

        # If the origin is not a tuple, then whatever is passed to the default will be
        # used as-id, so we don't need to worry about matching length.
        if not isinstance(self.org, tuple):
            return

        if not isinstance(self.default, tuple) or len(self.org) != len(self.default):
            raise ValueError("Length of defaults does not equal length of origins")


@dataclass
class CleanData:
    coord: InitVar[Coordinate]

    org_list: List[Course] = field(default_factory=list, init=False)
    dst_list: List[Optional[Course]] = field(default_factory=list, init=False)
    default_list: List[Any] = field(default_factory=list, init=False)
    value: Any = field(default=None, init=False)

    exceptions: List[Union[NullNameError, NonNavigableError]] = (
        field(default_factory=list)
    )

    def __post_init__(self, coord: Coordinate) -> None:

        if isinstance(coord.org, tuple):
            self.org_list.extend(coord.org)
        else:
            self.org_list.append(coord.org)

        if coord.default is NO_DEFAULT:
            self.default_list.extend(NO_DEFAULT for _ in self.org_list)
        elif isinstance(coord.default, tuple):
            self.default_list.extend(coord.default)
        else:
            self.default_list.append(coord.default)

        if coord.dst is None:
            self.dst_list = [None] * len(self.org_list)
        elif isinstance(coord.dst, tuple):
            self.dst_list.extend(coord.dst)
        else:
            self.dst_list.append(coord.dst)


Coord: Type[Coordinate] = Coordinate
CleanerArgsType = List[Union[Optional[Course], Course, Coordinate]]


class Cartographer:
    def __init__(self) -> None:
        """
        Maps data from one object to another.

        Attributes:
          - **cache (** ``dict`` **):** dict for storing information
            during :func:`Cartographer.map`. The cache is cleared each time
            :func:`Cartographer.map` is run, and is available to :class:`Coordinate`
            cleaning functions and overridden :class:`Cartographer` cleaning functions.

        Primary interaction is through :func:`Cartographer.map`, which iterates over a
        ``list`` of :class:`Coordinate` objects, fetching data from ``origin_root`` and
        placing on ``dst_root``.
        """
        self.cache: dict = dict()

    def clean_org(self, course: Course, coordinate: Coordinate) -> Course:
        """
        Makes alterations to ``coordinate.org``.

        :param course: course to clean
        :param coordinate: coordinate to process
        :return: origin Course to be used for :func:`Course.fetch.`

        Designed to be over-ridden for custom parsing. Function is not static to allow
        for access to ``self.cache``.

        **default behavior:** Passes origin :class:`Course` through, making no
        alterations.
        """
        return course

    def clean_dst(self, course: Optional[Course], coordinate: Coordinate) -> Course:
        """
        Makes alterations to ``coordinate.dst``.

        :param course: course to clean
        :param coordinate: coordinate to process
        :return: Destination Course to be used for :func:`Course.place`

        Designed to be overridden for custom parsing. Function is not static to allow
        for access to ``self.cache``.

        **default behavior:** Passes destination :class:`Course` through, making no
        alterations.  If ``coordinate.dst`` is ``None``, ``coordinate.org`` is copied,
        replacing all bearings with the :class:`Fallback` type.
        """
        if course is None:
            course = Course(*(Fallback(x) for x in coordinate.clean.org_list[0]))
        return course

    def clean_value(self, values: Any, coordinate: Coordinate) -> Any:
        """
        Makes alterations to the value of a coordinate.

        :param values: value or values to clean
        :param coordinate: coordinate to process
        :return: Value to be used in :func:`Course.place`

        Designed to be over-ridden for custom parsing. Function is not static to allow
        for access to ``self.cache``.

        **default behavior:** Passes ``value`` through, making no alterations.
        """
        return values

    def map(
        self,
        origin_root: Any,
        dst_root: Any,
        coordinates: Optional[Iterable[Coordinate]] = None,
        surveyor: Optional[Surveyor] = None,
        exceptions: bool = True,
    ) -> None:
        """
        Map data from one object to another.

        :param origin_root: root source data is pulled from
        :param dst_root: Mutable root destination data is applied to
        :param coordinates: coordinates instructing how to transfer each
            piece of data
        :param surveyor: surveyor object for automatic coordinate mapping
        :param exceptions:
            - ``True``: raise :class:`NullNameError` and :class:`NonNavigableError`
            - ``False``: suppress until end, then raise :class:`SuppressedErrors`

        :raises NullNameError: when Course cannot be found
        :raises NonNavigableError: If surveyor cannot chart object.
        :raises SuppressedErrors: At end if errors occur and ``exceptions`` is set
            to ``False``

        :return: ``None`` Data is applied in-place.

        See documentation for further details and examples.
        """

        if coordinates is None:
            coordinates = tuple()

        # We need to make empty clean data here in case these coords are being re-used.
        for coord in coordinates:
            object.__setattr__(coord, "clean", CleanData(coord))

        # Map the explicitly passed coordinates.
        mapped_courses, error_list = _map_coordinates(
            self, origin_root, dst_root, coordinates, exceptions
        )

        # Auto-map remaining coordinates if applicable.
        if surveyor is not None:
            survey_errors = _chart_survey(
                self, origin_root, dst_root, surveyor, exceptions, mapped_courses
            )
            error_list.extend(survey_errors)

        # Raise any suppressed errors.
        if error_list:
            to_raise = SuppressedErrors("Some errors occurred while mapping")
            to_raise.errors = error_list
            raise to_raise


# ##### HELPER FUNCTIONS #####
# These functions help with the mapping operations, in order to Cartographer from
#   getting cluttered
def _get_cleaner(
    self_func: Callable, coord: Coordinate, coord_func: Optional[Callable], cache: dict
) -> Tuple[Callable, list]:
    """Gets the cleaner for a course or value, and sets up the args"""
    # Coordinate cleaners take precedence
    if coord_func is not None:
        cleaner: Callable = coord_func
        cleaner_args: list = [coord, cache]
    else:
        # Then Cartographer cleaners, they act as the default
        cleaner = self_func
        cleaner_args = [coord]

    return cleaner, cleaner_args


def _clean_courses(
    courses: Union[List[Optional[Course]], List[Course]],
    cleaner: Callable,
    cleaner_args: CleanerArgsType,
) -> None:
    """cleans all courses of type with course cleaner function"""
    for course, i in zip(courses, itertools.count()):
        these_args = cleaner_args.copy()
        these_args.insert(0, course)
        cleaned = cleaner(*these_args)
        courses[i] = cleaned


def _fetch_org_value(cart: Cartographer, origin_root: Any, coord: Coordinate) -> Any:
    """Gets value or values from coordinate.org"""
    cleaner, cleaner_args = _get_cleaner(
        cart.clean_org, coord, coord.clean_org, cart.cache
    )
    _clean_courses(coord.clean.org_list, cleaner, cleaner_args)

    origin_default = zip(coord.clean.org_list, coord.clean.default_list)
    value = tuple(c.fetch(origin_root, default=d) for c, d in origin_default)

    if len(coord.clean.org_list) <= 1:
        # If there's only one course, we DON'T return values as a tuple.
        value = value[0]

    return value


def _place_dst_value(
    cart: Cartographer, destination_root: Any, coord: Coordinate
) -> None:
    """places value at destination course(s)"""
    cleaner, cleaner_args = _get_cleaner(
        cart.clean_dst, coord, coord.clean_dst, cart.cache
    )

    _clean_courses(coord.clean.dst_list, cleaner, cleaner_args)

    values = coord.clean.value

    # if there is only one destination we are going to wrap the value in a tuple so that
    #   we can iterate in either situation.
    if len(coord.clean.dst_list) <= 1:
        values = (values,)

    for value, this_dst in zip(values, coord.clean.dst_list):
        if this_dst is None:
            continue

        this_dst.place(destination_root, value)


def _map_coordinate(
    cart: Cartographer, origin_root: Any, destination_root: Any, coord: Coordinate
) -> None:
    """
    Process coordinate: apply source data to destination data

    :param origin_root: root source object data is pulled from
    :param destination_root: root destination object data is applied to
    :param coord: coordinate data instructing how to transfer one piece of data

    :raises NullNameError: when Course cannot be found
    :raises SuppressedMapErrors: At end if errors occur and ``exceptions`` is set
        to false
    :return: None. ``destination`` is edited in place.
    """
    # fetch origin value(s)
    if coord.clean.value is None:
        coord.clean.value = _fetch_org_value(cart, origin_root, coord)

    # clean value(s)
    cleaner, cleaner_args = _get_cleaner(
        cart.clean_value, coord, coord.clean_value, cart.cache
    )

    cleaner_args.insert(0, coord.clean.value)
    coord.clean.value = cleaner(*cleaner_args)

    # place value(s) at destinations(s)
    _place_dst_value(cart, destination_root, coord)


def _map_coordinates(
    cart: Cartographer,
    origin_root: Any,
    dst_root: Any,
    coordinates: Iterable[Coordinate],
    exceptions: bool,
) -> Tuple[List[Course], List[Union[NullNameError, NonNavigableError]]]:
    """Maps the explicitly passed coordinates."""
    mapped: List[Course] = list()
    error_list: List[Union[NullNameError, NonNavigableError]] = list()

    for coordinate in coordinates:
        try:
            _map_coordinate(cart, origin_root, dst_root, coordinate)
        except NullNameError as error:
            if exceptions:
                raise error
            error_list.append(error)
        else:
            mapped.append(coordinate.clean.org_list[0])

    return mapped, error_list


def _map_survey_chart(
    cart: Cartographer,
    origin_root: Any,
    dst_root: Any,
    exceptions: bool,
    mapped_courses: List[Course],
    course_chart: List[Tuple[Course, Any]],
) -> List[Union[NullNameError, NonNavigableError]]:
    """
    Survey origin_root and map data to dst_root if courses have not been mapped already.
    """
    error_list: List[Union[NullNameError, NonNavigableError]] = list()

    for course, value in course_chart:
        if any(course in x for x in mapped_courses):
            continue
        if any(x in course for x in mapped_courses):
            continue

        coordinate = Coordinate(org=course)
        object.__setattr__(coordinate, "clean", CleanData(coordinate))
        coordinate.clean.value = value

        try:
            _map_coordinate(cart, origin_root, dst_root, coordinate)
        except NullNameError as error:
            if exceptions:
                raise error
            error_list.append(error)

        mapped_courses.append(course)

    return error_list


def _chart_survey(
    chart: Cartographer,
    origin_root: Any,
    dst_root: Any,
    surveyor: Surveyor,
    exceptions: bool,
    mapped_courses: List[Course],
) -> List[Union[NullNameError, NonNavigableError]]:
    """Makes a chart of origin_root's courses"""
    error_list: List[Union[NullNameError, NonNavigableError]] = list()

    try:
        course_chart = surveyor.chart(origin_root, exceptions=exceptions)
    except SuppressedErrors as error:
        error_list.extend(error.errors)
        # if we get a SuppressedErrors, we can recover a partial chart
        course_chart = error.chart_partial

    # reverse sort by length so that deeper elements are attempted first, then
    #   parents are skipped if mapping is successful
    course_chart.sort(key=lambda x: len(x), reverse=True)

    survey_errors = _map_survey_chart(
        chart, origin_root, dst_root, exceptions, mapped_courses, course_chart
    )
    error_list.extend(survey_errors)

    return error_list
