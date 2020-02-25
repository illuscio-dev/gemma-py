import pytest

from gemma import SuppressedErrors, NullNameError, NonNavigableError


@pytest.mark.parametrize(
    "suppressed,check_type",
    [
        ([NullNameError()], NullNameError),
        ([NullNameError(), NullNameError()], NullNameError),
        ([NullNameError(), NonNavigableError()], NullNameError),
        ([NullNameError(), NonNavigableError()], NonNavigableError),
        ([NullNameError(), NonNavigableError(), NullNameError()], NonNavigableError),
        ([NullNameError(), NonNavigableError(), NullNameError()], NullNameError),
    ],
)
def test_suppressed_errors_type_check(suppressed, check_type):
    error = SuppressedErrors()
    error.errors = suppressed

    assert issubclass(check_type, error.types)
