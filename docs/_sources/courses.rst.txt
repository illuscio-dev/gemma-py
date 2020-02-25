.. automodule:: gemma

.. _Courses:

Courses: Data as Paths
======================

Courses are the main way ``gemma`` fetches and places data.

Course Class
------------

.. autoclass:: Course
   :special-members: __init__
   :members:

Making a New Course Object
--------------------------

Each ``*arg`` becomes one bearing in the new course:

>>> from gemma import Course, Item, Attr, Fallback
>>>
>>> new_course = Course(Item("a"), Item(2))
>>> new_course
<Course: <Item: 'a'> / <Item: 2>>

Course supports `pathlib-like syntax`_ to declare bearings via the ``/``
operator.

>>> path_like = Course() / Item("a") / Item(2)
>>> path_like
<Course: <Item: 'a'> / <Item: 2>>

Bearings will be automatically cast from other values using the :func:`bearing` factory.

>>> auto_cast = Course() / 5 / "method()" / "[item]" / "@attr"
>>> auto_cast
<Course: <Item: 5> / <Call: 'method'> / <Item: 'item'> / <Attr: 'attr'>

:func:`bearing` is passed the list of courses in ``Course.BEARINGS_EXTENSION`` added to
``Course.BEARINGS``.

By default, ``Course.BEARINGS`` contains :class:`Item`, :class:`Call`, :class:`Attr`,
and :class:`Fallback` in that order, and ``Course.BEARING_EXTENSION`` is empty, a
placeholder for custom bearings when :class:`Course` is inherited to extend
functionality.

Appending Courses
-----------------

*Courses are immutable*. Whenever an item is added to the end of a course, a
new course object is returned.

>>> original = Course() / Item("a") / Item(2)
>>> extended = original / Item("additional")
>>>
>>> original
<Course: <Item: 'a'> / <Item: 2>>
>>> extended
<Course: <Item: 'a'> / <Item: 2> / <Item: 'additional'>>

``original`` is not modified when ``Item("additional")`` is added to it; it returns a
new :class:`Course` object.

Courses can be appended to other Courses:

>>> course_one = Course() / 1 / 2
>>> course_two = Course() / 3 / 4
>>> course_one / course_two
<Course: <Item: 1> / <Item: 2> / <Item: 3> / <Item: 4>>

The PORT Course
---------------

``gemma`` comes with a blank course called ``PORT`` ( all good courses start in
port! ), which can be imported and used as the root of pathlib-like courses
instead of using ``Course()``:

>>> new_course = PORT / "@a" / 2
>>> new_course
<Course: <Attr: 'a'> / <Item: 2>>
>>> second_course = PORT / "[key]" / 10
>>> second_course
<Course: <Item: 'key'> / <Item: 10>>

Since ``PORT`` is immutable, it can be used over and over to indicate the
declaration of a new course with fewer keystrokes.

Course Length
-------------

Check the number of bearings in a :class:`Course` using ``len()``:

>>> two_long = PORT / "first" / "second"
>>> two_long
<Course: <Fallback: 'first'> / <Fallback: 'second'>>
>>> len(two_long)
2
>>> three_long = two_long / "third"
>>> three_long
<Course: <Fallback: 'first'> / <Fallback: 'second'> / <Fallback: 'third'>>
>>> len(three_long)
3

PORT is an empty :class:`Course` used for initialization, so appending two bearings
results in a :class:`Course` of length ``2``, not ``3``.

Iterating Through a Course
--------------------------

You can easily iterate through a course's bearings like any other iterable.

>>> example = PORT / 1 / "[two]" / "@three"
>>> for this_bearing in example:
...     print(repr(this_bearing))
...
<Item: 1>
<Item: 'two'>
<Attr: 'three'>

Course Equality
---------------

:class:`Course` objects are equal when each's :func:`BearingAbstract.fetch`
or :func:`BearingAbstract.place` would have the same effect.

- Courses are equal if the bearings they contain at each index are equal.
    >>> course_one = PORT / Item(-1) / Attr("text")
    >>> course_two = PORT / -1 / "@text"
    >>> course_one == course_two
    True

    Because they would get the same data:

    >>> from gemma.test_objects import test_objects
    >>> simple, data_dict, data_list, structured, target = test_objects()
    >>>
    >>> course_one.fetch(data_list)
    'in a list'
    >>> course_two.fetch(data_list)
    'in a list'

    example object refs: :ref:`simple`

- Courses of different lengths are unequal.
    >>> course_three = course_one / Attr("additional")
    >>> print(
    ...     len(course_one),
    ...     len(course_three),
    ...     course_one == course_three
    ... )
    2 3 False

    They would fetch different data.

- Courses with different bearing names are not equal.
    >>> course_one = PORT / Item(-1) / Attr("text")
    >>> course_two = PORT / Item(-1) / Attr("number")
    >>> course_one == course_two
    False

    They fetch different data.

    >>> course_one = PORT / Item(-1) / Attr("text")
    >>> course_two = PORT / Item(-1) / Attr("number")
    >>> course_one.fetch(data_list)
    'in a list'
    >>> course_two.fetch(data_list)
    20

- Courses with different bearing types are not equal.
    >>> course_items = PORT / Item("nested") / Item('one key')
    >>> course_attrs = PORT / Attr("nested") / Attr("one key")
    >>> course_attrs == course_items
    False

    They fetch different data.

    >>> course_items.fetch(data_dict)
    1
    >>> course_attrs.fetch(data_dict)
    Traceback (most recent call last):
        ...
    gemma._exceptions.NullNameError: @nested

- :class:`Fallback` can be equal to other bearing types.
    ... depending on what other bearing types are loaded into it's
    ``.BEARING_CLASSES`` field.

    >>> course_items = PORT / Item("nested") / Item("one key")
    >>> course_bearings = PORT / Fallback("nested") / Fallback("one key")
    >>> course_items == course_bearings
    True

    Both these courses would fetch the same data on the same objects, so
    they are equal.

    >>> course_items.fetch(data_dict)
    1
    >>> course_bearings.fetch(data_dict)
    1

Slicing and Indexing
--------------------

- You can get a bearing at a specific Index like so:
    >>> example = PORT / 0 / "[one]" / "@two" / "three()"
    >>> example[1]
    <Item: 'one'>
    >>> example[-1]
    <Call: 'three'>

- Slices will return a new :class:`Course` with the requested bearings:
    >>> example[1:3]
    <Course: <Item: 'one'> / <Attr: 'two'>>

- :func:`Course.parent` will return a course to the parent.
    >>> example.parent
    <Course: <Item: 0> / <Item: 'one'> / <Attr: 'two'>>

- :func:`Course.end_point` will return the last bearing.
    >>> example.end_point
    <Call: 'three'>

.. _contains:

Checking for a Sub-Course or Bearing
------------------------------------

- Check if one course contains another.
    >>> course_example = PORT / "[one]" / "[two]" / "[three]" / "[four]"
    >>> course_middle = PORT / "[two]" / "[three]"
    >>> course_middle in course_example
    True
    >>> course_other = PORT / "[one]" / "[three]"
    >>> course_other in course_example
    False

- Check if a course contains a bearing.
    >>> Item("two") in course_example
    True
    >>>
    >>> Item("five") in course_example
    False

- Check if a course begins with a Sub-Course or Bearing.
    >>> course_start = PORT / "[one]" / "[two]"
    >>> course_example.starts_with(course_start)
    True
    >>> course_example.starts_with(Item("one"))
    True
    >>> course_example.starts_with(course_middle)
    False
    >>> course_example.starts_with(Item("three"))
    False

- Check if a course ends with a Sub-Course or Bearing.
    >>> course_end = PORT / "[three]" / "[four]"
    >>> course_example.ends_with(course_end)
    True
    >>> course_example.ends_with(Item("four"))
    True
    >>> course_example.ends_with(course_middle)
    False
    >>> course_example.ends_with(Item("three"))
    False

- Checking for Sub-Courses follows the same rules as equality above.
    Bearings can be equal to other types.

    >>> example_is_bearings = PORT / "one" / "two" / "three" / "four"

    The above uses all bearings so will contain courses of different types.

    >>> example_is_bearings = PORT / "one" / "two" / "three" / "four"
    >>>
    >>> test_course_attrs = PORT / Attr("two") / Attr("three")
    >>> test_course_items = PORT / Item("two") / Item("three")
    >>>
    >>> test_course_attrs in example_is_bearings
    True
    >>> test_course_items in example_is_bearings
    True

    But ``test_course_items`` would not contain ``test_course_attrs``
    because the bearings are not of equal types.

    >>> test_course_attrs in test_course_items
    False

Fetching Default Values
-----------------------

Courses can return a default value if the course does not exist on a target object.

    >>> data = {"nested": {"one": 1}}
    >>> course = PORT / "nested" / "three"
    >>>
    >>> course.fetch(data)
    Traceback (most recent call last):
        ...
    gemma._exceptions.NullNameError: [3]
    >>>
    >>> course.fetch(data, default=3)
    3

Creating Missing Bearings
-------------------------

By passing a type to the ``factory`` of a bearing, you can generate missing types during
a :func:`Course.place` operation.

>>> from gemma import PORT, Item, Attr
>>>
>>> data = {}
>>> has_factory = PORT / Item("list", factory=list) / 0
>>> has_factory.place(data, "value")
>>> data
{'list': ['value']}

``Item("list")`` would normally throw ``NullNameError``, but when ``factory`` is not
set to None, the error is caught. A new instance of the ``factory`` type is placed
at the missing bearing. Traversal then continues as normal.

Factories can be chained:

>>> data = {}
>>> chained = PORT / Item("list", factory=list) / Item(0, factory=dict) / "key"
>>> chained.place(data, "value")
>>> data
{'list': [{'key': 'value'}]}

This *does not* work with :func:`Course.fetch`. Factories cannot be used with shorthand.

Factories do not only catch :class:`NullNameError`, but also replace values of the wrong
type.

>>> data = {"list": None}
>>> replaces_none = PORT / Item("list", factory=list) / 0
>>> replaces_none.place(data, "value")
>>> data
{'list': ['value']}

This allows for arbitrary stand-ins to represent no data: None, Null, etc. Some caution
is required, as ``factory`` may replace valid data if the type is incorrect.

>>> data = {"nested": ["zero", "one", "two"]}
>>> wrong_factory = PORT / "nested" / Item(0, factory=dict)
>>> wrong_factory.place(data, "whoops")
>>> data
{'nested': {0: 'whoops'}}

The existing ``list`` under "nested" is replaced with a new ``dict``. Factories do not
replace bearings of the same type, so to fix this:

>>> data = {"nested": ["zero", "one", "two"]}
>>> right_factory = PORT / "nested" / Item(0, factory=list)
>>> right_factory.place(data, "yay!")
>>> data
{'nested': ['yay!', 'one', 'two']}

:func:`BearingAbstract.init_factory` can be overridden to alter how a factory is
initialized.

More fetch() Examples
---------------------

Additional example 1a:
    >>> from gemma import Attr, Call, Fallback, Item, PORT
    >>> from gemma.test_objects import test_objects
    >>>
    >>> simple, data_dict, data_list, structured, target = test_objects()
    >>>
    >>> example_one = (
    ...     PORT / Attr("list_data") / Item(-3) / Item("simple") / Attr("text")
    ... )
    >>> example_one.fetch(structured)
    'string value'

    example object refs: :ref:`structured`

Additional example 1b:
    Remember that course can auto-cast bearings based on their string cues, so
    the above can be rewritten as:

    >>> example_cast = PORT / "@list_data" / -3 / "[simple]" / "@text"
    >>> example_cast.fetch(structured)
    'string value'

    example object refs: :ref:`structured`

Additional example 1c:
    Even simpler, as:

    >>> example_fallback = PORT / "list_data" / -3 / "simple" / "text"
    >>> example_fallback.fetch(structured)
    'string value'

    Comparing ``example_cast`` and ``example_fallback`` you will see the second has cast
    to the :class:`Fallback` type.

    >>> example_cast
    <Course: <Attr: 'list_data'> / <Item: -3> / <Item: 'simple'>
    / <Attr: 'text'>>
    >>> example_fallback
    <Course: <Fallback: 'list_data'> / <Item: -3> / <Fallback: 'simple'>
    / <Fallback: 'text'>>

    The exact types cannot be determined through shorthand. In most cases, this is
    acceptable, and trades a slight performance hit for more readable, faster to create
    code.

    example object refs: :ref:`structured`

Additional example 2:
    A :class:`BearingAbstract` type of the wrong kind will raise a
    :class:`NullNameError` exception.

    >>> wrong_type = (
    ...     PORT / Attr("list_data") / Item(-3) / Attr("simple") / Attr("text")
    ... )
    >>> wrong_type.fetch(structured)
    Traceback (most recent call last):
        ...
    gemma._exceptions.NullNameError: @simple

    The object ``Attr("simple")`` is to act on has a key called ``"simple"``; It does
    not have an attribute called ``simple``, which :func:`Attr.fetch` is looking for.

    example object refs: :ref:`structured`

- Additional example 3a:
    Lets fetch data from the ``keys()`` method of a dictionary.

    >>> with_method = PORT / Attr("dict_data") / Call("keys")
    >>> with_method.fetch(structured)
    dict_keys(['a', 'b', 1, 2, 'nested', 'simple'])

    example object refs: :ref:`structured`

- Additional example 3b:
    The above can be auto-cast like so:

    >>> with_method_cast = PORT / "dict_data" / "keys"
    dict_keys(['a', 'b', 1, 2, 'nested', 'simple'])

    Be careful. :func:`Item.fetch` is attempted before :func:`Call.fetch`, so if the
    dict has a key called ``keys`` there may be odd results:

    >>> data = {"nested": {"keys": "uh-oh"}}
    >>> ambiguous = PORT / "nested" / "keys"
    >>> ambiguous.fetch(data)
    'uh-oh'

    To fix this, you can use a string-cue to indicate the last bearing should
    be cast to :class:`Call` instead of :class:`Item`.

    >>> more_clear = PORT / "nested" / "keys()"
    >>> more_clear.fetch(data)
    dict_keys(['keys'])

    Now, what if there is actually a KEY we want to get called ``"keys()"``,
    parentheses and all?

    >>> confusing_data = {"nested": {"keys()": "butwhytho?"}}

    In this case, we should cast to :class:`Item` explicitly, to avoid the detection of
    the ``()`` convention that :class:`Call` uses as shorthand.

    >>> most_clear = PORT / "nested" / Item("keys()")
    >>> most_clear.fetch(confusing_data)
    'butwhytho?'

    Auto-casting is a powerful feature for saving time, but one must keep in
    mind the ambiguity it can introduce in certain edge-cases.

.. web links
.. _pathlib-like syntax: https://docs.python.org/3/library/pathlib.html#operators