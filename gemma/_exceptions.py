from typing import List, Union, Iterable, Tuple, Any, Type


class NullNameError(BaseException):
    """Bearing cannot be found on object."""


class NonNavigableError(BaseException):
    """Target object cannot be traversed"""


class SuppressedErrors(BaseException):
    """
    Errors occurred while Cartographer mapped data

    Attributes:
        - **errors (** ``List[BaseException]`` **):** list of errors which occurred.

        - **chart_partial (** ``List[Tuple["Course", Any]]`` **):** If raised from
          :func:`Surveyor.chart` raising a NonNavigableError for some elements, a
          partial chart of the successfully traversed data will be stored here.
    """

    def __init__(self, *args: Iterable):
        super().__init__(*args)
        self.errors: List[Union[NullNameError, NonNavigableError]] = list()
        self.chart_partial: List[Tuple["Course", Any]] = list()

    @property
    def types(self) -> Tuple[Union[Type[NonNavigableError], Type[NullNameError]], ...]:
        """
        Types of errors in ``SuppressedErrors.errors`` to be used for isinstance()
        checks.

        :return: error types
        """
        types = set(type(x) for x in self.errors)
        return tuple(types)


typing_help = False
if typing_help:
    from ._course import Course  # noqa: F401
