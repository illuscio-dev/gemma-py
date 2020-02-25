from gemma import Course
from ._xelm_bearing import XElm


class XCourse(Course):
    BEARINGS_EXTENSION = [XElm]


XPATH: XCourse = XCourse()
