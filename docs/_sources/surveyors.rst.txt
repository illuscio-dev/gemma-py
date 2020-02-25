.. automodule:: gemma

.. _Surveyors:

Surveyors: Traverse Structures
==============================

Surveyors chart nested data, using chained :class:`Compass` objects to build
(:class:`Course`, value) pairs

Surveyor Class
--------------

.. autoclass:: Surveyor
   :special-members: __init__
   :members:

Get all Courses in Object
-------------------------

>>> from gemma import Surveyor
>>> from gemma.test_objects import test_objects
...
... simple, data_dict, data_list, structured, target = test_objects()
>>> default = Surveyor()
>>>
>>> for course, value in default.chart_iter(data_dict):
...     print(repr(course), '|', value)
...
<Course: <Item: 'a'>> | a dict
<Course: <Item: 'b'>> | b dict
<Course: <Item: 1>> | one dict
<Course: <Item: 2>> | two dict
<Course: <Item: 'nested'>> | {'one key': 1, 'two key': 2}
<Course: <Item: 'nested'> / <Item: 'one key'>> | 1
<Course: <Item: 'nested'> / <Item: 'two key'>> | 2
<Course: <Item: 'simple'>> | DataSimple(text='string value', number=40)
<Course: <Item: 'simple'> / <Attr: 'text'>> | string value
<Course: <Item: 'simple'> / <Attr: 'number'>> | 40

example object refs: :ref:`data_dict`

Charting with Custom Compasses
------------------------------

>>> keys = ['a', 'b', 'nested']
>>> dict_compass = Compass(target_types=dict, items=keys)
>>>
>>> custom = Surveyor(compasses=[dict_compass])
>>> for course, value in custom.chart_iter(data_dict):
...     print(repr(course), value)
...
<Course: <Item: 'a'>> a dict
<Course: <Item: 'b'>> b dict
<Course: <Item: 'nested'>> {'one key': 1, 'two key': 2}

Only ``"a"``, ``"b"``, and ``"nested"`` are returned. Why did the :class:'Surveyor' not
recurse into ``"nested"``, instead returning only the first layer?

Because we have supplied only one :class:`Compass -- *tied to all ``dict``objects* --
that returns keys for ``"a"``, ``"b"``, and ``"nested"`` *only*. Lets override
:class:`Compass` and set a better filter for when it should be used, something
more granular than type.

>>> class DictDataCompass(Compass):
...     def __init__(self):
...         keys = ['a', 'b', 'nested']
...         super().__init__(target_types=dict, items=keys)
...
...     def is_navigable(self, target):
...         if not super().is_navigable(other):
...             return False
...         if 'nested' in other:
...             return True
...         else:
...             return False
...

We override :func:`Compass.is_navigable`, checking that ``target`` is a ``dict`` through
the ``super()`` call, then confirm the ``"nested"`` key exists -- the defining
characteristic of our target ``dict``.

We also override ``__init__`` to restrict our return keys rather than doing it every
time this compass is initialized.

Lets load it into a :class:`Surveyor` and try to chart ``dict_data`` again.

>>> dict_data_compass = DictDataCompass()
>>> custom = Surveyor(compasses=[dict_data_compass])
>>>
>>> for course, value in custom.chart_iter(data_dict):
...     print(repr(course), value)
...
<Course: <Item: 'a'>> a dict
<Course: <Item: 'b'>> b dict
<Course: <Item: 'nested'>> {'one key': 1, 'two key': 2}
Traceback (most recent call last):
    ...
gemma._exceptions.NonNavigableError: could not find compass for f{'one ...

A :class:`NonNavigableError` once the surveyor hits ``'nested'``. Why?

Because we have only supplied a :class:`Compass` that can handle ``dict_data``,
but no :class:`Compass` that can handle a generic ``dict``.

Lets use the default :class:`Compass`. We list it after ``DictDataCompass``, so
the default is not chosen first for every object. Surveyor uses the first compatible
:class:`Compass` it finds.

>>> default_compass = Compass()
>>> custom = Surveyor(compasses=[dict_data_compass, default_compass])
>>> for course, value in custom.chart_iter(data_dict):
...     print(repr(course), value)
...
<Course: <Item: 'a'>> a dict
<Course: <Item: 'b'>> b dict
<Course: <Item: 'nested'>> {'one key': 1, 'two key': 2}
<Course: <Item: 'nested'> / <Item: 'one key'>> 1
<Course: <Item: 'nested'> / <Item: 'two key'>> 2

Now we get the full chart.

We can use ``compasses_extra`` to add our special :class:`Compass` before the default
automatically.

>>> custom = Surveyor(compasses_extra=[dict_data_compass])
>>>
>>> simple, data_dict, data_list, structured, target = test_objects()
>>> for course, value in custom.chart_iter(data_dict):
...     print(repr(course), value)
...
<Course: <Item: 'a'>> a dict
<Course: <Item: 'b'>> b dict
<Course: <Item: 'nested'>> {'one key': 1, 'two key': 2}
<Course: <Item: 'nested'> / <Item: 'one key'>> 1
<Course: <Item: 'nested'> / <Item: 'two key'>> 2

The default :class:`Compass` is used for any objects ``compasses_extra`` doesn't catch.

example object refs: :ref:`data_dict`

Adding Additional End Points
----------------------------

The surveyor needs to know how it recognizes where a course should terminate, and has a
tuple of types it will not traverse into.

The default types are: ``(str, int, float, type)``. Additional types can be anything
capable of an ``isinstance()`` check.

In the last example, ``data_dict`` contains a Dataclass, "DataSimple". Lets say we don't
wish to recurse into DataSimple, instead treating it as primary data type.

We can add it as an additional end points type as so:

>>> from gemma.test_objects import DataSimple
>>> more_end_points = Surveyor(end_points_extra=(DataSimple,))
>>> for course, value in more_end_points.chart_iter(data_dict):
...     print(repr(course), value)
...
<Course: <Item: 'a'>> a dict
<Course: <Item: 'b'>> b dict
<Course: <Item: 1>> one dict
<Course: <Item: 2>> two dict
<Course: <Item: 'nested'>> {'one key': 1, 'two key': 2}
<Course: <Item: 'nested'> / <Item: 'one key'>> 1
<Course: <Item: 'nested'> / <Item: 'two key'>> 2
<Course: <Item: 'simple'>> DataSimple(text='string value', number=40)

The resulting courses do not dig further then the "simple" key.

Like ``compasses`` and ``compasses_extra``, you can change or remove the default end
points using the ``end_points`` keyword argument.

To see why endpoints are important, try removing ``str`` as an endpoint
and chart a dict with string values.

Suppressing NonNavigableError
-----------------------------

It may be useful in certain situations to get a partial map, suppressing
:class:`NonNavigableError` exceptions instead of throwing them and not returning.

The ``exceptions`` keyword will suppress errors until the end of the operation.
Lets take a look at the normal way:

>>> from gemma import Compass, Surveyor
>>>
>>> dict_compass = Compass(target_types=dict)
>>> data = {
...     'a': 'a value',
...     'list': [1, 2, 3],
...     'dict': {'b': 'b value'}
... }
...
>>> for x in raises_non_navigable.chart_iter(data):
...     print(repr(x))
...
(<Course: <Item: 'a'>>, 'a value')
(<Course: <Item: 'list'>>, [1, 2, 3])
Traceback (most recent call last):
    ...
gemma._exceptions.NonNavigableError: could not find compass for f[1, 2, 3]

At the ``"list"`` key, we throw an error -- our surveyor cannot traverse
lists with the provided compasses.

Lets set ``exceptions`` to ``False`` to suppress the exception and continue
charting.

>>> for x in raises_non_navigable.chart_iter(data, exceptions=False):
...     print(repr(x))
...
(<Course: <Item: 'a'>>, 'a value')
(<Course: <Item: 'list'>>, [1, 2, 3])
(<Course: <Item: 'dict'>>, {'b': 'b value'})
(<Course: <Item: 'dict'> / <Item: 'b'>>, 'b value')
Traceback (most recent call last):
    ...
gemma._exceptions.SuppressedErrors: some objects could not be charted

The surveyor finished before raising a :class:`SuppressedErrors` exception. It can't
traverse into the  ``list``, and moves past it.

When using :func:`Surveyor.chart` instead of :func:`Surveyor.chart_iter`, you can
recover a partial list from ``SuppressedErrors.chart_partial``.

>>> from gemma import SuppressedErrors
>>>
>>> try:
...     chart = raises_non_navigable.chart(data, exceptions=False)
... except SuppressedErrors as error:
...     print(error.chart_partial)
...
[(<Course: <Item: 'a'>>, 'a value'), (<Course: <Item: 'list'>>, [1, 2, 3]), ...

Get a list of the Suppressed errors:

>>> try:
...     chart = raises_non_navigable.chart(data, exceptions=False)
... except SuppressedErrors as error:
...     print(error.errors)
...
[NonNavigableError('could not find compass for f[1, 2, 3]')]
