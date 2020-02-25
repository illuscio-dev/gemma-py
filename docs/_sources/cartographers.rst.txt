.. automodule:: gemma

.. _Cartographers:

Cartographers: Move Data
========================

Cartographers map one object's data to another. Individual mapping instructions are
stored in :class:`gemma.Coordinate` dataclasses.

Coordinate Dataclass
--------------------

.. class:: Coordinate

    Stores instructions for a single data point transfer. This object is immutable,
    and will always retain the values originally passed to it. If you are accessing it
    through a cleaning function, and wish to get any values cleaned in previous steps,
    they will be found on the ``Coordinate.clean`` object.

    **Fields: __init__**
      - **org (** :class:`Course` **):** Course to :func:`Course.fetch` ``value`` on
        origin data structure

         - Optional (Can be ``None``)
         - Default: ``None``
         - Can be passed tuple to pull from multiple origins.

      - **dst (** :class:`Course` **):** Course to :func:`Course.place` ``value`` on
        destination data structure

         - Optional: (Can Be ``None``)
         - Default: ``None``
         - Can be passed tuple to place on multiple destinations.

      - **clean_origin (** ``Callable`` **):** function to alter ``org`` before
        :func:`Course.fetch`

         - Optional: (Can Be ``None``)
         - Default: ``None``

      - **clean_dst (** ``Callable`` **):** function to alter ``dst`` before
        :func:`Course.place`

         - Optional: (Can be ``None``)
         - Default: ``None``

      - **clean_value (** ``Callable`` **):** function to alter ``value`` before
        :func:`Course.place`

         - Optional: (Can be ``None``)
         - Default: ``None``

      - **default (** ``Any`` **):** default value(s) to use if origin course(s) do not
        exist

         - Default: ``NO_DEFAULT``
         - Can be passed tuple to when there are multiple origins. Use NO_DEFAULT flag
           for any origin that should throw an error if it does not exist.

    **Fields: __post_init__**
      - **clean (** :class:`CleanData` **):** stores cleaned origin courses, destination
        courses, and value for Coordinate as it is being processed.


.. class:: CleanData

    Stores cleaned values during processing of a coordinate. Instances of this class
    are made by the :class:`Coordinate` class, and are nor meant to be created on their
    own.

    **Fields: __post_init__**

      - **org_list (** List[Course] **):** list of :class:`Course` objects passed to
        ``Coordinate.org``. Always a list, even if a single ``Course`` is passed to
        ``org``

        - Default: ``list``

        The courses in this field are replaced by their cleaned versions as the
        :class:`Coordinate` is processed.

      - **dst_list (** List[Optional[Course]] **):** list of :class:`Course` objects
        passed to ``Coordinate.dst``. Always a list, even if a single ``Course`` is
        passed to ``dst``

        - Default: ``list``

        The courses in this field are replaced by their cleaned versions as the
        :class:`Coordinate` is processed.

      - **value (** ``Callable`` **):** value fetched from origin course, and to be
        placed at destination course.


Coord Alias
-----------

``gemma`` comes with a built-in alias for :class:`Coordinate` called ``Coord``, for more
compact code.

>>> from gemma import Coordinate, Coord
>>> Coordinate is Coord
True

Cartographer Class
------------------

.. autoclass:: Cartographer
    :special-members: __init__
    :members:

Mapping Flow
------------

The flow of the overall :func:`Cartographer.map` function is as follows:

    #. Clear `Cartographer.cache`

    #. Map each explicit :class:`Coordinate` with below logic.

    #. If ``surveyor`` is passed, use :func:`Surveyor.chart` on ``origin_root``.

    #. Iterate through endpoint :class:`Course` objects from surveyor.

        - Each ( :class:`Course`, ``value`` ) is placed into the ``origin``, ``value``
          of new :class:`Coordinate` objects.

        - Each :class:`Coordinate` follows steps below

The logic flow for mapping each :class:`Coordinate` is as follows:

  #. Each ``coordinate.org`` is altered by the ``coordinate.clean_org`` function
     individually. Or if it is not supplied, the :func:`Cartographer.clean_org` method.
     Results are returned to ``coordinate.clean.org_list``.

  #. All values objects are fetched from the ``coordinate.clean.org_list`` courses and
     placed on ``coordinate.clean.value``. If there are multiple origin courses, all
     of their values are returned as a ``tuple`` in order. If ``coordinate.default``
     is not NO_DEFAULT, it will be used to supply missing values.

  #. If a :class:`NullNameError` is thrown above, it is either raised or suppressed and
     saved for later depending on the map operation settings.

  #. ``coordinate.clean.value`` is altered by the ``coordinate.clean_value`` function.
     Or, if it is not supplied, the :func:`Cartographer.clean_value` method. All values
     are passed to the cleaning function, not individually.

  #. ``coordinate.dst`` is altered by the ``coordinate.clean_dst`` function.
     Or if it is not supplied, the :func:`Cartographer.clean_dst` method. Results are
     returned to ``coordinate.clean.dst_list``

  #. :func:`Course.place` of each ``coordinate.clean.dst_list`` sets
     ``coordinate.clean.value`` on ``dst_root``. If mote than one destination course is
     specified, the values is iterated over, placing an item in order on each
     destination course.

Features
--------

Lets set up the root and destination objects we will use for the first few
examples:

>>> from gemma import Cartographer, Coordinate, PORT
>>> from dataclasses import dataclass
>>> from collections import defaultdict
>>> import json
>>>
>>> @dataclass
... class DataOrigin:
...     a: str = "a value"
...     b: str = "b value"
...     one: int = 1
...     two: int = 2
...
>>> data_origin = DataOrigin()
>>> data_destination = defaultdict(defaultdict)


Basic Mapping
-------------

>>> coordinates = [
...     Coordinate(org=PORT / "a", dst=PORT / "str" / "a field"),
...     Coordinate(org=PORT / "b", dst=PORT / "str" / "b field"),
...     Coordinate(org=PORT / "one", dst=PORT / "int" / "one field"),
...     Coordinate(org=PORT / "two", dst=PORT / "int" / "two field"),
... ]
...

For compactness, we can write the above like so:

>>> from gemma import Coord
>>> coordinates = [
...     Coord(org=PORT / "a", dst=PORT / "str" / "a field"),
...     Coord(org=PORT / "b", dst=PORT / "str" / "b field"),
...     Coord(org=PORT / "one", dst=PORT / "int" / "one field"),
...     Coord(org=PORT / "two", dst=PORT / "int" / "two field"),
... ]
...

... using the ``Coord`` alias.

>>> data_cartographer = Cartographer()
>>> data_cartographer.map(data_origin, data_destination, coordinates)
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
}


Using Default Values
--------------------

We can supply default values for coordinates in the case that they do not exist:

>>> coordinates = [
...     Coord(org=PORT / "a", dst=PORT / "str" / "a field"),
...     Coord(org=PORT / "b", dst=PORT / "str" / "b field"),
...     Coord(org=PORT / "one", dst=PORT / "int" / "one field"),
...     Coord(org=PORT / "two", dst=PORT / "int" / "two field"),
...     Coord(org=PORT / "three", dst=PORT / "int" / "three field", default=3),
... ]
...
>>> data_cartographer = Cartographer()
>>> data_cartographer.map(data_origin, data_destination, coordinates)
>>>
>>> print(json.dumps(data_destination, sort_keys=True, indent=4))
{
  "int": {
      "one field": 1,
      "two field": 2
      "three field": 3
  },
  "str": {
      "a field": "a value",
      "b field": "b value"
  }
}

Supply Cleaning Functions
-------------------------

We wish to cast ``DataOrigin.one`` and ``DataOrigin.two`` to ``str`` objects. Lets
supply a cleaning function.

>>> def cast_string(value, coord: Coordinate, cache: dict) -> str:
...    return str(value)

Notice the signature here. *All :class:`Coordinate` cleaning functions must follow this
signature*.
    
    - ``values/course``, is the current value or course being processed. Course-cleaning
      functions always pass one course at a time, regardless of whether it is a
      one-to-one or many-to-many mapping. Value-cleaning functions pass all values from
      all origin courses as a tuple, rather than one at a time.
    - ``coord``, is the Coordinate for the value,course being processed.
    - ``cache`` is passed ``Cartographer.cache`` of the running process so information
      can be stored or referenced during the process.

Each method should return its relevant value; :class:`Coordinate` objects *should not*
be edited in place within the function. ``coordinate.clean_origin`` and
``coordinate.clean_dst`` *must* return an :class:`Course` object.

Lets use ``cast_string()`` on the appropriate coordinates:

>>> coordinates = [
...     Coordinate(org=PORT / "a", dst=PORT / "str" / "a field"),
...     Coordinate(org=PORT / "b", dst=PORT / "str" / "b field"),
...     Coordinate(
...         org=PORT / "one",
...         dst=PORT / "int" / "one field",
...         clean_value=cast_string
...     ),
...     Coordinate(
...         org=PORT / "two",
...         dst=PORT / "int" / "two field",
...         clean_value=cast_string
...     ),
... ]
...
>>> data_cartographer = Cartographer()
>>> data_cartographer.map(data_origin, data_destination, coordinates)
>>>
>>> print(json.dumps(data_destination, sort_keys=True, indent=4))
{
  "int": {
      "one field": "1",
      "two field": "2"
  },
  "str": {
      "a field": "a value",
      "b field": "b value"
  }
}

Blank Destinations
------------------

By default, leaving the destination path empty results in the Cartographer placing
the ``Coordinate.value`` at the same course as the source, using :class:`Fallback`
bearings instead of the original bearing types.

Lets map the ``simple`` test object to a dict without explicit destination
coordinates.

>>> from gemma.test_objects import test_objects
>>>
>>> simple, data_dict, data_list, structured, target = test_objects()
>>>
>>> simple_coordinates = [
...     Coordinate(org=PORT / "text"),
...     Coordinate(org=PORT / "number")
... ]
>>>
>>> cart = Cartographer()
>>> destination = dict()
>>>
>>> cart.map(simple, destination, simple_coordinates)
>>> destination
{'text': 'simple text', 'number': 50}

example object refs: :ref:`simple`

Map Source Automatically
------------------------

Supplying a :class:`Surveyor` to :func:`Cartographer.map` automatically discovers
endpoints and transfers them to the destination at the same bearing names.

>>> survey = Surveyor()
>>> destination = dict()
>>>
>>> cart.map(simple, destination, surveyor=survey)
>>> destination
{'text': 'simple text', 'number': 50}

See the :ref:`Surveyors` and :ref:`Compasses` sections for more information on how
to control what endpoints a :class:`Surveyor` will discover when charting a data
structure.

example object refs: :ref:`simple`

Mix Explicit and Automatic Mapping
----------------------------------

You can use both explicit and automatic coordinate mapping in concert. Explicitly
mapped coordinates will not be mapped a second time if :class:`Surveyor` discovers them.

>>> coordinates = [
...     Coord(org=PORT / "text", dst=PORT / "custom key"),
... ]
>>>
>>> destination = dict()
>>> cart.map(simple, destination, coordinates, surveyor=survey)
>>>
>>> destination
{'custom key': 'simple text', 'number': 50}

example object refs: :ref:`simple`

Override Default Methods
------------------------

There are thee main ways to influence how data is moved from
``origin_root`` to ``destination_root``:

  - Alter the :class:`Course` fetching the ``value``
  - Alter the ``value`` that was fetched.
  - Alter the :class:`Course` placing the ``value``

As seen in example two, each of these values can be altered on a per-:class:`Coordinate`
basis by passing cleaning functions.

We can also override the :class:`Cartographer` cleaning methods to change the default
behavior. Lets try altering all origin courses.

We have some data in a ``dict``:

>>> photo_info = {
...     "cannon.resolution.width": 1920,
...     "cannon.resolution.height": 1080,
...     "cannon.file.name": "my_photo_1234",
...     "cannon.file.extension": "jpg"
... }

It's annoying to have to write "cannon." at the beginning of every coordinate,
Ideally we could write something like this:

>>> coordinates = [
...     Coordinate(org=PORT / "resolution.width"),
...     Coordinate(org=PORT / "resolution.height"),
...     Coordinate(org=PORT / "file.name"),
...     Coordinate(org=PORT / "file.extension"),
... ]

It's both quicker and easier to read!

By default, if there is no destination course given, a generic version of the
source course will be used. But what if we want to split up the data into separate
``"resolution"`` and `"file"` sub-dictionaries?

Lets override :func:`Cartographer.clean_org` to add the `"cannon."` back to thee
head before fetching the source data, and :func:`Cartographer.clean_dst` to create
the appropriate destination :class:`Course`.

>>> class NewCart(Cartographer):
...
...     def clean_org(self, course: Course, coordinate: Coordinate) -> Course:
...         origin = coordinate.org
...         new_name = "cannon." + origin.end_point.name
...
...         new_origin = origin.with_end_point(Item(new_name))
...         return new_origin
...
...     def clean_dst(self, course: Course, coordinate: Coordinate) -> Course:
...         if coordinate.dst is not None:
...             return coordinate.dst
...         destination = coordinate.org
...
...         dst_name: str = destination.end_point.name
...         bearing_names = dst_name.split(".")
...
...         new_bearings = (Item(x) for x in bearing_names if x != "cannon")
...         new_destination = Course(*new_bearings)
...
...         return new_destination
...
>>> cart = NewCart()
>>> destination = defaultdict(defaultdict)
>>>
>>> cart.map(photo_info, destination, surveyor=survey)
>>> print(json.dumps(destination, sort_keys=True, indent=4))
{
  "file": {
      "extension": "jpg",
      "name": "my_photo_1234"
  },
  "resolution": {
      "height": 1080,
      "width": 1920
  }
}

One/Many Origins to One/Many Destinations
-----------------------------------------

The ``org`` and ``dst`` :class:`Coordinate` fields can accept a ``tuple`` of courses.

When multiple origin courses are passed, a ``tuple`` of their values will be passed to
the value cleaning function.

When multiple destination courses are passed, the result of the value cleaning function
will be iterated through, passing values in order to each destination.

Lets say we have some information about a photo:

>>> photo_info = {
...     "width": 1920,
...     "height": 1080,
... }

And we want to map it to a single "resolution" field. Lets set up a cleaning function
that takes width and height, then returns a formatted resolution:

>>> from typing import Tuple
>>> def resolution_str(values: Tuple[int, int], coord: Coordinate, cache: dict) -> str:
...     return f"{values[0]}x{values[1]}"

We expect ``values`` will be a ``tuple`` with two ``int`` values: width and height.
Lets pass *two* :class:`Course` objects to the ``org`` parameter of a single
:class:`Coordinate`..

>>> coords = [
...     Coordinate(
...         org=(
...             PORT / "[width]",
...             PORT / "[height]"
...         ),
...         dst = PORT / "[resolution]",
...         clean_value=resolution_str
...     )
... ]

The return of ``format_resolution()`` will be placed onto the single ``dst``
:class:`Course`

>>> cart.map(photo_info, destination, coords)
>>> destination
{'resolution': '1920x1080'}

When we have multiple origins we can supply multiple defaults:

>>> coords = [
...     Coordinate(
...         org=(
...             PORT / "[width]",
...             PORT / "[height]"
...         ),
...         dst = PORT / "[resolution]",
...         clean_value=resolution_str,
...         default=(1280, 720)
...     )
... ]
...
>>> cart.map(dict(), destination, coords)
>>> destination
{'resolution': '1280x720'}

If you only wish SOME of the origins to have a default supply a ``NO_DEFAULT`` flag for
the origins you wish to still throw errors when a valid course is not present.

>>> from gemma import NO_DEFAULT
>>>
>>> coords = [
...     Coordinate(
...         org=(
...             PORT / "[width]",
...             PORT / "[height]"
...         ),
...         dst = PORT / "[resolution]",
...         clean_value=resolution_str,
...         default=(1280, NO_DEFAULT)
...     )
... ]

The above will not throw an error if ``"width"`` is missing, but will if ``"height"``
is.

Lets do the other way around, splitting up a ``"resolution"`` field into ``"width"`` and
``"height"``:

>>> def split_res(value: str, coord: Coordinate, cache: dict) -> Tuple[int, int]:
...     width, height = values.split("x")
...     return int(width), int(height)
...
>>> coords = [
...     Coordinate(
...         org = PORT / "[resolution]",
...         dst = (
...             PORT / "[width]",
...             PORT / "[height]"
...         ),
...         clean_value=split_res
...     )
... ]
>>>
>>> destination = dict()
>>> cart.map(photo_info, destination, coords)
>>> destination
{'width': 1920, 'height': 1080}

Many-to-many relationships are possible as well, following the same logic.

Suppress Errors
---------------

:class:`Cartographer` throws an error when hitting an origin or destination
:class:`Course` that does not exist.

>>> from gemma import Cartographer, Surveyor, Coordinate, Compass, PORT
>>>
>>> data = {
...     "a": "a value",
...     "c": "c value"
... }
>>> destination = dict()
>>>
>>> coords = [
...     Coordinate(org=PORT / "a"),
...     Coordinate(org=PORT / "b"),
...     Coordinate(org=PORT / "c"),
... ]
>>> cart = Cartographer()
>>>
>>> cart.map(data, destination, coords)
Traceback (most recent call last):
    ...
gemma._exceptions.NullNameError: <Fallback: 'b'>

``"b"`` is a bad key, so mapping stops at the error. ``"c"`` is unmapped.

>>> destination
{'a': 'a value'}

:func:`Cartographer.map` will suppress :class:`NullNameError` and
:class:`NonNavigableError` exceptions when ``exceptions`` is set to ``False``, waiting
until the operation is complete to throw :class:`SuppressedErrors`.

>>> destination = dict()
>>> cart.map(data, destination, coords, exceptions=False)
Traceback (most recent call last):
    ...
gemma._exceptions.SuppressedErrors: Some errors occurred while mapping

The error is thrown at the end of the mapping, ``destination`` is as complete as
possible:

>>> destination
{'a': 'a value', 'c': 'c value'}

To see what errors occurred, catch the exception and check ``SuppressedErrors.errors``:

>>> from gemma import SuppressedErrors
>>> try:
...     cart.map(data, destination, coords, exceptions=False)
... except SuppressedErrors as error:
...     print(error.errors)
...
[NullNameError("<Fallback: 'b'>")]

Setting errors to ``False`` also catches :class:`NonNavigableError`. We can use
``isinstance`` on :func:`SuppressedErrors.types` to check what types are present.

>>> try:
...     cart.map(data, destination, coords, exceptions=False)
... except SuppressedErrors as error:
...     print("NonNavigableError:", isinstance(error.types, NonNavigableError))
...     print("NullNameError:", isinstance(error.types, NullNameError))
...
NonNavigableError: False
NullNameError: False
