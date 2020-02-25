.. automodule:: gemma

.. _Compasses:

Compasses: Describe Objects
===========================

Compass Class
-------------

.. autoclass:: Compass
   :special-members: __init__
   :members:

Map Bearings of Object
----------------------

Get all (:class:`Item`, value) pairs of dict:

>>> from gemma import Compass
>>> from gemma.test_objects import test_objects
...
... simple, data_dict, data_list, structured, target = test_objects()
>>>
>>> default_compass = Compass()
>>>
>>> for bearing in default_compass.bearings_iter(data_dict):
...     print(bearing)
...
(<Item: 'a'>, 'a dict')
(<Item: 'b'>, 'b dict')
(<Item: 1>, 'one dict')
(<Item: 2>, 'two dict')
(<Item: 'nested'>, {'one key': 1, 'two key': 2})
(<Item: 'simple'>, DataSimple(text='string value', number=40))

By default, compass returns all non-callable attributes and items.
``dict`` does not support attrs, so only :class:`Item` objects and their values are
returned.

Alternatively :func:`Compass.bearings` returns the results as a ``list``,
rather than a ``Generator``.

>>> default_compass.bearings(data_dict)
[(<Item: 'a'>, 'a dict'), (<Item: 'b'>, 'b dict'), ...

example object refs: :ref:`data_dict`

Include Methods of Object
-------------------------

By default, methods of ``target`` are not returned. We have to explicitly allow them
by name.

>>> keys_compass = Compass(calls=['keys'])
>>>
>>> for bearing in keys_compass.bearings_iter(data_dict):
...     print(bearing)
...
(<Item: 'a'>, 'a dict')
(<Item: 'b'>, 'b dict')
(<Item: 1>, 'one dict')
(<Item: 2>, 'two dict')
(<Item: 'nested'>, {'one key': 1, 'two key': 2})
(<Item: 'simple'>, DataSimple(text='string value', number=40))
(<Call: 'keys'>, dict_keys(['a', 'b', 1, 2, 'nested', 'simple'])

This is to avoid a compass automatically executing a method like
``dict.pop()`` as it traverses an object.

example object refs: :ref:`data_dict`

Omitting Bearings from Map
--------------------------

>>> keys_only_compass = Compass(
...     target_types=dict, items=False, calls=["keys"]
... )
>>>
>>> keys_only_compass.bearings(data_dict)
[(<Call: 'keys'>, dict_keys(['a', 'b', 1, 2, 'nested', 'simple']))]

By passing ``False`` to items, we stop any :class:`Item` bearings from being
returned. The same behavior applies to ``attrs`` and ``methods``

example object refs: :ref:`data_dict`

.. _restrict-bearings:

Restrict Bearings from Map
--------------------------

Lets say we have a compass that extracts specific info we want about pets
from a form. Here is our form data:

>>> pet = {
...     "type": "pet",
...     "name": "fluffy",
...     "age": 7,
...     "species": "cat",
...     "owner": {
...         "name": "Joe",
...         "age": 25,
...         "other_pets":[
...             2345332,
...             1244553,
...             6455666
...         ]
...     }
... }

Now, we only need to grab name, age and species. The owner info is not
important to us, and is at least two additional layers that do not need to
be traversed.

We could set up a compass, and to get those bearings like so:

>>> target_keys = ["name", "age", "species"]
>>> pet_compass = Compass(items=target_keys)
>>>
>>> pet_compass.bearings(pet)
[(<Item: 'name'>, 'fluffy'), (<Item: 'age'>, 7), (<Item: 'species'>, 'cat')]

Declare Compatible Types
------------------------

In the keys example above, we may want to signal to a :class:`Surveyor`
object that a compass should only be used with certain types.

>>> dict_compass = Compass(target_types=dict, calls=["keys"])

``target_types`` allows us to signal that only dicts can be passed to this
compass.

Now when we check if a data structure can be navigated by this compass:

>>> dict_compass.is_navigable(data_dict)
True
>>> dict_compass.is_navigable(structured)
False

The dict passes, but the dataclass does not. If we try to navigate each, the
dataclass will throw a :class:`NonNavigableError`

>>> dict_compass.bearings(data_dict)
[(<Item: 'a'>, 'a dict'), (<Item: 'b'>, 'b dict'), (<Item: 1>, ...
>>> dict_compass.bearings(structured)
Traceback (most recent call last):
    ...
gemma._exceptions.NonNavigableError: Compass cannot map DataStructured(...

example object refs: :ref:`data_dict`
example object refs: :ref:`structured`

Custom Compatibility
--------------------

What if we want to be more specific about what a compass can navigate?

Using the pet form example from :ref:`restrict-bearings`, we could restrict the compass
to only act on ``dict`` objects:

>>> target_keys = ["name", "age", "species"]
>>> pet_compass = Compass(target_types=dict, items=target_keys)

However, this compass will act on any dict:

>>> not_a_pet = {
...     "type": "car",
...     "name": "blue",
...     "make": "toyota",
...     "model": "camry",
...     "age": 7
... }
>>>
>>> pet_compass.bearings(not_a_pet)
[(<Item: 'name'>, 'blue'), (<Item: 'age'>, 7)]

What we must do is create a new compass type and override
:func:`Compass.is_navigable`.

>>> class PetCompass(Compass):
...     def __init__(self):
...         target_keys = ["name", "age", "species"]
...         super().__init__(target_types=dict, items=target_keys)
...
...     def is_navigable(self, target: Any) -> bool:
...         try:
...             dict_type = target["type"]
...         except (KeyError, TypeError):
...             return False
...
...         if dict_type == "pet":
...             return True
...         else:
...             return False

We've also altered ``__init__`` to pass our target type and restricted items.

Now when we check if each ``dict`` is navigable:

>>> pet_compass = PetCompass()
>>> pet_compass.is_navigable(pet)
True
>>> pet_compass.is_navigable(not_a_pet)
False

And when we try to get the bearings for each:

>>> pet_compass.bearings(pet)
[(<Item: 'name'>, 'fluffy'), (<Item: 'age'>, 7), (<Item: 'species'>, 'cat')]
>>> pet_compass.bearings(not_a_pet)
Traceback (most recent call last):
    ...
gemma._exceptions.NonNavigableError: PetCompass cannot map {'type': 'car'...

Additional Examples
-------------------

Traversing a Dataclass.
    >>> default_compass = Compass()
    >>> for bearing in default_compass.bearings_iter(structured):
    ...     print(bearing)
    ...
    (<Attr: 'a'>, 'a data')
    (<Attr: 'b'>, 'b data')
    (<Attr: 'one'>, 31)
    (<Attr: 'two'>, 32)
    (<Attr: 'dict_data'>, {'a': 'a dict', 'b': 'b dict', 1: 'one dict', ...
    (<Attr: 'list_data'>, ['zero list', 'one list', 'two list', ...
    (<Attr: 'simple'>, DataSimple(text=None, number=None))

Compasses can be extended in other ways. For more information on extending the
Compass type, see: :ref:`Custom-Compasses`
