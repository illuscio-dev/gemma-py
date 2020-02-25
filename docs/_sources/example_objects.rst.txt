.. _test-objects:

Example Objects
===============

``gemma`` comes pre-loaded with some example data objects used throughout this
documentation. To make a fresh copy of these objects, copy/paste the following: ::

   from gemma.test_objects import test_objects

   simple, data_dict, data_list, structured, target = test_objects()

For details on each object, see the documentation of :func:`test_objects`, and
the descriptions following.

.. autofunction:: gemma.test_objects.test_objects

.. _simple:

simple
------

``simple`` is a ``dataclass`` object of the following class.

>>> @dataclass
... class DataSimple:
...     text: Optional[str] = None
...     number: Optional[int] = None

The instantiated object returned by this function is equivalent to:

>>> simple = DataSimple("simple text", 50)
>>> simple
DataSimple(text='simple text', number=50)

.. _data_dict:

data_dict
---------

``data_dict`` is a ``dict``, with the following data:

>>> data_dict = {
...     "a": "a dict",
...     "b": "b dict",
...     1: "one dict",
...     2: "two dict",
...     "nested": {"one key": 1, "two key": 2},
...     "simple": DataSimple("string value", 40),
... }

.. _data_list:

data_list
---------

``data_list`` is a list with the following data:

>>> data_list = [
...     "zero list",
...     "one list",
...     "two list",
...     "three list",
...     data_dict,
...     [10, 11, 12, 13],
...     DataSimple("in a list", 20),
... ]

The ``data_dict`` here is a copy of ``data_dict``; the two are not the same mutable
object.

.. _structured:

structured
----------

``structured`` is an instance of the following dataclass:

>>> @dataclass
... class DataStructured:
...     a: Optional[str] = "a data"
...     b: Optional[str] = "b data"
...     one: Optional[int] = 31
...     two: Optional[int] = 32
...     dict_data: dict = field(default_factory=dict)
...     list_data: list = field(default_factory=list)
...     simple: DataSimple = field(default_factory=DataSimple)
...

The instantiated object returned by this function is equivalent to:

>>> structured = DataStructured(dict_data=data_dict, list_data=data_list)

... where ``data_dict`` is a separate copy of the same ``data_dict`` returned by
this function and ``data_list`` is the same for ``data_list``.

.. _target:

target
------

``target`` is a dataclass with empty objects designed to be a target for setting data.
The class is:

>>> @dataclass
... class DataTarget:
...     text_target: Optional[str] = None
...     number_target: Optional[int] = None
...     list_target: list = field(default_factory=list)
...     dict_target: dict = field(default_factory=dict)
...

And the returned object is equivalent to:

>>> target = DataTarget()
>>> target
DataTarget(text_target=None, number_target=None, list_target=[], dict_target={})