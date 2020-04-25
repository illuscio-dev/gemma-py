.. automodule:: gemma

.. _Bearings:

Bearings: Access Data Generically
=================================

A bearing details how to fetch or place data of a given ``name`` on a target object.

E.g., you would fetch ``name`` from a dict using ``dict[name]``, but for a dataclass
using ``data.name``.

Bearings are the building blocks of a :class:`Course` objects, which fetch/place a
sequence of bearings on a complex data structure.

.. _bearing-abstract:

BearingAbstract Base Type
-------------------------

:class:`BearingAbstract` outlines the methods and attributes that must/may be overridden
by implementations.

=====================================  =============  ==========  =================================
name                                   type           required?   description
=====================================  =============  ==========  =================================
:func:`BearingAbstract.fetch`          method         yes         Gets data from object at ``name``
:func:`BearingAbstract.place`          method         yes         Sets data on object at ``name``
``__str__``                            method         yes         String shorthand
``NAME_TYPES``                         cls attribute  encouraged  Compatible ``name`` ``type`` (s)
``REGEX``                              cls attribute  encouraged  String shorthand pattern
:func:`BearingAbstract.is_compatible`  method         no          Can ``name`` be cast to bearing?
:func:`BearingAbstract.name_from_str`  method         no          Converts string to ``name`` value
:func:`BearingAbstract.init_factory`   method         no          Returns initialized factory_type
=====================================  =============  ==========  =================================


.. autoclass:: gemma.BearingAbstract
   :special-members: __init__
   :members:

Bearing Shorthand
-----------------

The default implementations of :class:`BearingAbstract` checks for the following
patterns when determining if a string can be cast to it's type:

=================   =========   ==================
class               shorthand   note
=================   =========   ==================
:class:`Attr`       @name
:class:`Item`       [name]
:class:`Call`       name()
:class:`Fallback`   name        accepts all values
=================   =========   ==================

>>> from gemma import Attr
>>>
>>> attribute = Attr.from_string('name')
Traceback (most recent call last):
    ...
ValueError: text does not match regex
>>> attribute = Attr.from_string('@name')
>>> attribute.name
'name'

This is slightly different from instantiating the class directly, which does
not check/parse the input value of a string, instead using whatever it is fed.

>>> attribute = Attr('name')
>>> attribute.name
'name'
>>> attribute = Attr('@name')
>>> attribute.name
'@name'

Likewise, ``str(BearingAbstract)`` should return the properly formatted shorthand
through ``BearingAbstract.__str__``

>>> from gemma import Attr, Item, Call, Bearing
>>>
>>> str(Attr("a"))
'@a'
>>> str(Item("a"))
'[a]'
>>> str(Call("a"))
'a()'
>>> str(Fallback("a"))
'a'

This allows for string-encoded bearings which can be easily cast by :class:`Course`
objects. For example:

>>> from gemma import Course
>>>
>>> data = {'nested': {'a': 'a value', 'b': 'b value'}}
>>>
>>> to_fetch = Course() / '[nested]' / 'keys()'
>>> to_fetch.fetch(data)
dict_keys(['a', 'b'])

:class:`Course` auto-casts strings using a configurable factory method.

:func:`BearingAbstract.from_string` can be overridden when implementing a
custom Bearing if more granularity is needed than setting the class' ``REGEX`` field.

Implementations
---------------

``gemma`` comes with four implementations of :class:`BearingAbstract`, covering most
basic data object API's.

.. _attr:

Attr Type
#########
.. autoclass:: Attr
   :members: fetch, place

   Attr fetches and places data on a target's attribute.

   **inherits from:** :class:`BearingAbstract`

   **name types:** Attr only accepts ``str`` as ``name`` value.

   **shorthand:** ``"@name"``

.. _Item:

Item Type
#########

.. autoclass:: Item
   :members:

   Item fetches and places data on a target's index or mapping

   **inherits from:** :class:`BearingAbstract`

   **name types:** ``Any``.

   **shorthand:** ``"[name]"``

.. _Call:

Call Type
#########

.. autoclass:: Call
   :special-members: __init__
   :members:

   Call fetches and sets data through a target's ``target.name()`` method.

   **inherits from:** :class:`BearingAbstract`

   **name types:** Call only accepts ``str`` as ``name`` values.

   **shorthand:** ``"name()"``

.. _Bearing:

Fallback Type
#############

.. autoclass:: Fallback
    :special-members: __init__
    :members:

.. _bearing-cast:

Casting Bearings
----------------

When casting a bearing directly, formatting is not parsed, unlike the method that
:func:`bearing` below uses.

>>> from gemma import Item
>>>
>>> Item("[has_brackets]")
<Item: '[has_brackets]'>
>>>
>>> Item("no_brackets")
<Item: 'no_brackets'>

Values must pass the class' :func:`BearingAbstract.is_compatible`, if it does
not, ``TypeError`` is raised.

>>> from gemma import Attr
>>>
>>> Attr(10)
Traceback (most recent call last):
 ...
TypeError: type <class 'int'> not allowed as <class 'gemma._bearings.Attr'>

When passing a bearing to another bearing, the original's
:func:`BearingAbstract.name` value is extracted before casting.

>>> original = Item('key_name')
>>> Attr(original)
<Attr: 'key_name'>

.. _bearing-sort:

Sorting Bearings
----------------

Bearings are sorted in the following order:

* By class ``type``:

  * :class:`Item`
  * :class:`Attr`
  * :class:`Call`
  * [custom classes]
  * :class:`Fallback`

* Custom classes are sorted by class ``__name__``
* Each class group is sorted by it's value type's ``__name__``
* Within each value type, values are sorted by their respective sort methods.

Lets look as how the following list of bearings is sorted:

>>> from gemma import Item, Attr, Call, Fallback, BearingAbstract

We're going to make a couple custom bearings to demonstrate how they sort:

>>> class Alpha(BearingAbstract):
...     pass
...
>>> class Beta(BearingAbstract):
...     pass
...

Here are our unsorted values:

>>> bearing_unsorted = [
...     Fallback("b"),
...     Call("b"),
...     Alpha("b"),
...     Attr("b"),
...     Fallback("a"),
...     Item("b"),
...     Call("a"),
...     Beta("b"),
...     Item(2),
...     Alpha("a"),
...     Attr("a"),
...     Item("a"),
...     Attr("a"),
...     Beta("a"),
...     Item(1)
... ]
...

Sort them:

>>> bearings_sorted = sorted(bearing_unsorted)

Print sorted list to check:

>>> for this_bearing in bearings_sorted:
...     print(repr(this_bearing))
...
<Item: 1>
<Item: 2>
<Item: 'a'>
<Item: 'b'>
<Attr: 'a'>
<Attr: 'a'>
<Attr: 'b'>
<Call: 'a'>
<Call: 'b'>
<Alpha: 'a'>
<Alpha: 'b'>
<Beta: 'a'>
<Beta: 'b'>
<Fallback: 'a'>
<Fallback: 'b'>

.. _bearing-eq:

Checking Bearing Equality
-------------------------

- Bearings of the same type and :func:`BearingAbstract.name` value are considered equal:
    >>> Attr('a') == Attr('a')
    True

- Bearings with different :func:`BearingAbstract.name` values are unequal.
    >>> Attr('a') == Attr('b')
    False

- Bearings of different types are always unequal.
    >>> Attr('a') == Item('a')
    False

- Except the :class:`Fallback` class... sometimes
    The :class:`Fallback` class is equal to any type loaded into its ``BEARING_CLASSES``
    field. By default, this makes it equal to any :class:`Item`, :class:`Attr`,
    :class:`Call` or :class:`Fallback` with the same :func:`BearingAbstract.name` value.

    >>> Fallback('a') == Attr('a')
    True
    >>>
    >>> Fallback('a') == Item('a')
    True
    >>>
    >>> Fallback('a') == Call('a')
    True

    However, if we define an arbitrary class named ``Alpha``, it will not be equal to
    a bearing with the same name.

    >>> class Alpha(BearingAbstract):
    ...     pass
    ...
    >>> Fallback('a') == Alpha('a')
    False

    If we create a Bearing with the :func:`bearing` factory method detailed below,
    using Alpha as one of its possibilities, the two values will be equal.

    >>> from gemma import bearing
    >>>
    >>> new_bearing = Fallback('a', bearing_classes=[Attr, Fallback, Alpha])
    >>> new_bearing
    <Fallback: 'a'>
    >>> new_bearing == Alpha("a")
    True

    This is because :func:`bearing` loads any fallback :class:`Fallback`
    objects ``.BEARING_CLASSES`` field with the classes passed to ``bearing_classes``.

.. _bearing-factory:

Bearing Factory Method
----------------------

The factory method that most default ``gemma`` objects use when casting name values
to a bearing is:

.. autofunction:: bearing
