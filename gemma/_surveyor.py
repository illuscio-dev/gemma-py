from typing import List, Any

from ._compass import Compass, Optional, Generator, Type, Tuple, Union
from ._course import Course
from ._exceptions import NonNavigableError, SuppressedErrors


DEFAULT_COMPASSES: List[Compass] = [Compass()]
DEFAULT_END_POINTS: Tuple[Type, ...] = (str, int, float, type)


class Surveyor:
    def __init__(
        self,
        compasses: Optional[List[Compass]] = None,
        compasses_extra: Optional[List[Compass]] = None,
        end_points: Optional[Union[Tuple[Type, ...], Type]] = None,
        end_points_extra: Optional[Union[Tuple[Type, ...], Type]] = None,
        course_type: Type[Course] = Course,
    ):
        """
        Charts courses through data structure

        :param compasses: available compasses to navigate bearings
        :param compasses_extra: compasses to use in addition to defaults
        :param end_points: types where courses should terminate
        :param end_points_extra: end points to use in addition to defaults
        :param course_type: course class to use for course creation

        The main functionality for this course is through
        :func:`Surveyor.chart_iter` and :func:`Surveyor.chart`

        See below documentation for usage.
        """
        if compasses is None:
            compasses = DEFAULT_COMPASSES
        if compasses_extra is not None:
            compasses = compasses_extra + compasses

        if end_points is None:
            end_points = DEFAULT_END_POINTS
        if end_points_extra is not None:
            end_points += end_points_extra

        self._compasses: List[Compass] = compasses
        self._end_points: Union[Tuple[Type, ...], Type] = end_points
        self._course_type: Type[Course] = course_type

    def _choose_compass(self, target: Any) -> Compass:
        """
        Chooses compass for ``target`` from ``compasses`` list passed into __init__

        :param target: target to choose compass for
        :return: first compass object to pass :func:`Compass.is_navigable` for
            ``target`` object.
        """
        for compass in self._compasses:
            if compass.is_navigable(target):
                return compass
        raise NonNavigableError(f"could not find compass for f{repr(target)}")

    def _chart_layer(
        self, target: Any, parent_course: Course, exceptions: bool
    ) -> Generator[Union[Tuple[Course, Any], NonNavigableError], None, None]:
        """
        Charts a single object and it's sub-objects

        :param target: data_object to chart
        :param parent_course: parent Course to append bearings of ``target`` to.
        :param exceptions: Whether to suppress exceptions

        :return: yields :class:`Course`, value pairs for each bearing of
            ``target``.
        """
        try:
            compass = self._choose_compass(target)
        except NonNavigableError as error:
            if exceptions:
                raise error
            else:
                yield error
                return

        for bearing, value in compass.bearings_iter(target):
            bearing_course = parent_course / bearing
            yield bearing_course, value

            if value is None or isinstance(value, self._end_points):
                continue

            yield from self._chart_layer(value, bearing_course, exceptions)

    def chart_iter(
        self, target: Any, exceptions: bool = True
    ) -> Generator[Tuple[Course, Any], None, None]:
        """
        Charts data structure, yielding each (:class:`Course`, value) pair one at
        a time

        :param target: data structure to chart
        :param exceptions:
            - ``True``: Exceptions will be raised during process
            - ``False``: Exceptions will be suppressed and a :class:`SuppressedErrors`
              Error will be raised at the end.

        :return: yields :class:`Course`, value pairs

        :raises NonNavigableError: If a target is found that can't be navigated. This
            error will be suppressed if ``exceptions`` is set to ``False``
        :raises SuppressedErrors: Raised at end if ``NonNavigableError`` occurs and
            ``exceptions`` is set to ``False``

        See examples below.
        """
        root_course = self._course_type()
        exception_list: List[NonNavigableError] = list()

        for result in self._chart_layer(target, root_course, exceptions):
            if isinstance(result, NonNavigableError):
                exception_list.append(result)
            else:
                yield result

        if exception_list:
            error = SuppressedErrors("some objects could not be charted")
            error.errors.extend(exception_list)
            raise error

    def chart(self, target: Any, exceptions: bool = True) -> List[Tuple[Course, Any]]:
        """
        As :func:`Surveyor.chart_iter`, but returns all result pairs as list.

        :param target: data structure to chart
        :param exceptions:
            - ``True``: Exceptions will be raised during process
            - ``False``: Exceptions will be suppressed and a :class:`SuppressedErrors`
              Error will be raised at the end.

        :return: ``list`` of (:class:`Course`, value) pairs

        :raises NonNavigableError: If a target is found that can't be navigated. This
            error will be suppressed if ``exceptions`` is set to ``False``
        :raises SuppressedErrors: Raised at end if ``NonNavigableError`` occurs and
            ``exceptions`` is set to ``False`. Partial chart can be recovered from
            ``SuppressedErrors.chart_partial``

        See examples below.
        """
        chart: List[Tuple[Course, Any]] = list()

        try:
            for result in self.chart_iter(target, exceptions):
                chart.append(result)
        except SuppressedErrors as error:
            error.chart_partial = chart
            raise error

        return chart
