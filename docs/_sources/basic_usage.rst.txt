.. automodule:: gemma

.. _basic-usage:

Basic Usage
===========

Lay a :class:`Course` to your data!
   >>> from gemma import Course
   >>>
   >>> data = {
   ...     "a": [
   ...         None,
   ...         {"b": 2}
   ...     ]
   ... }
   >>>
   >>> data_course = Course("a", 1, "b")
   >>> data_course.fetch(data)
   2

Use `pathlib-like syntax`_ to work intuitively with :class:`Course` objects!
   The above is equivalent to:

   >>> root = Course()
   >>> data_course = root / "a" / 1 / "b"
   >>> data_course.fetch(data)
   2

Place data at a location!
   >>> data_course.place(data, "new value")
   >>> data
   {'a': [None, {'b': 'new value'}]}

Chart a structure's data!
   >>> from gemma import Surveyor
   >>> data_surveyor = Surveyor()
   >>> for course, value in data_surveyor.chart_iter(data):
   ...     print(repr(course), "|", value)
   ...
   <Course: <Item: 'a'>> | [None, {'b': 'new value'}]
   <Course: <Item: 'a'> / <Item: 0>> | None
   <Course: <Item: 'a'> / <Item: 1>> | {'b': 'new value'}
   <Course: <Item: 'a'> / <Item: 1> / <Item: 'b'>> | new value

Map data from one object to another with ease!
   Set up source data.

   >>> from dataclasses import dataclass
   >>>
   >>> @dataclass
   ... class DataOrigin:
   ...     a: str = "a value"
   ...     b: str = "b value"
   ...     one: int = 1
   ...     two: int = 2
   ...
   >>> data_origin = DataOrigin()

   Set up the object source data should be mapped to.

   >>> from collections import defaultdict
   >>> data_destination = defaultdict(dict)

   Create a quick list of input and output :class:`Course` objects. In this case, we
   want to map the above ``dataclass`` to a ``defaultdict`` with sub-dictionaries
   grouped by type

   >>> from gemma import Coordinate
   >>> root = Course()
   >>>
   >>> coordinates = [
   ...     Coordinate(org=root / "a", dst=root / "str" / "a field"),
   ...     Coordinate(org=root / "b", dst=root / "str" / "b field"),
   ...     Coordinate(org=root / "one", dst=root / "int" / "one field"),
   ...     Coordinate(org=root / "two", dst=root / "int" / "two field"),
   ... ]

   Map the data using a :class:`Cartographer` object. The data will be moved from the
   origin object :class:`Course` on the source object to the destination :class:`Course`
   on the destination object

   >>> from gemma import Cartographer
   >>> data_cartographer = Cartographer()
   >>> data_cartographer.map(data_origin, data_destination, coordinates)

   Check the result:

   >>> import json
   >>> print(json.dumps(data_destination, sort_keys=True, indent=4))
   {
       "int": {
           "one field": 1,
           "two field": 2
       },
       "str": {
           "a field": "a value",
           "b field": "b value"
       }
   }

   ``gemma`` makes it quick and easy to move data from one object to another in a quick,
   concise way. The example above is deterministic, so should not require manual
   creation of the input and output courses. The :class:`Cartographer` class allows for
   overriding of a few key methods to map data efficiently.

   >>> class NewCart(Cartographer):
   ...     def clean_dst(self, course: Course, coordinate: Coordinate) -> Course:
   ...         dst = Course(
   ...             type(coordinate.value).__name__,
   ...             (coordinate.origin.end_point.name + " field")
   ...         )
   ...         return dst

   The above method determines the destination course of each coordinate, in this
   example, we will use the default :class:`Surveyor`, which will allow the cartographer
   to find all the end points of ``data_origin`` on its own, then calculate each
   destination course.

   >>> data_cartographer = NewCart()
   >>>
   >>> data_destination = defaultdict(dict)
   >>> data_cartographer.map(data_origin, data_destination, surveyor=data_surveyor)
   >>>
   >>> print(json.dumps(data_destination, sort_keys=True, indent=4))
   {
    "int": {
        "one field": 1,
        "two field": 2
    },
    "str": {
        "a field": "a value",
        "b field": "b value"
    }

The deeper documentation will explain how each object works, and how it can be extended
for custom mapping. ``gemma`` offers an powerful, but straightforward method for
extending the library's functionality.

.. web links
.. _Gemma Frisius: https://en.wikipedia.org/wiki/Gemma_Frisius
.. _pathlib-like syntax: https://docs.python.org/3/library/pathlib.html#operators