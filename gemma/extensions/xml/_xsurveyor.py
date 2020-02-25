from gemma import Surveyor

from ._xcourse import XCourse
from ._xcompass import XCompass

xsurveyor = Surveyor(compasses_extra=[XCompass()], course_type=XCourse)
