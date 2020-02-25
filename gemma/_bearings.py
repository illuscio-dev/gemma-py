import re
from typing import (
    Any,
    TypeVar,
    Generic,
    Pattern,
    Union,
    Type,
    List,
    Tuple,
    Optional,
    Iterable,
    Dict,
)

from ._exceptions import NullNameError


_NameType = TypeVar("_NameType")
FactoryType = TypeVar("FactoryType")


class BearingAbstract(Generic[_NameType]):
    REGEX: Pattern = re.compile(".+")
    NAME_TYPES: List[Union[Type, Any]] = [str]

    def __new__(
        cls,
        name: Union[_NameType, "BearingAbstract[_NameType]"],
        *args: Iterable,
        factory: Optional[Type[FactoryType]] = None,
        **kwargs: dict,
    ) -> "BearingAbstract":

        if isinstance(name, BearingAbstract):
            name = name.name

        if not cls.is_compatible(name):
            raise TypeError(f"type {type(name)} not allowed as {cls}")

        new_bearing = object.__new__(cls)
        return new_bearing

    def __init__(
        self,
        name: Union[_NameType, "BearingAbstract[_NameType]"],
        factory: Optional[Type[FactoryType]] = None,
    ):
        """
        Abstract base class for :class:`Course` bearings.

        **inherits from:** ``Generic[_NameType]``

        :param name: name of key/index/attribute/method/etc to act on.
        :param factory: ``type`` to be used as default value if :func:`Course.place`
            hits empty or non-existent value so structure can be built

        Class-level Attributes
            - **REGEX**: ( ``re.Pattern`` ) - Regex pattern to match string shorthand
            - **NAME_TYPES** ( ``List[Union[Type, Any]]`` ) - ``type`` ( or ``tuple`` of
              types ) that ``name`` can be.
        """
        if isinstance(name, BearingAbstract):
            name = name.name
        self._name: _NameType = name
        self._factory: Optional[Type[FactoryType]] = factory

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, BearingAbstract):
            raise TypeError("bearings cannot be compared to other types")

        if not other.name == self.name:
            return False
        if isinstance(other, Fallback) and type(self) in other.BEARING_CLASSES:
            return True
        if isinstance(self, Fallback) and type(other) in self.BEARING_CLASSES:
            return True
        if isinstance(other, type(self)):
            return True
        if isinstance(self, type(other)):
            return True
        else:
            return False

    def __lt__(self, other: "BearingAbstract") -> bool:
        return self._sort_key(self) < self._sort_key(other)

    def __le__(self, other: "BearingAbstract") -> bool:
        return self._sort_key(self) <= self._sort_key(other)

    def __gt__(self, other: "BearingAbstract") -> bool:
        return self._sort_key(self) > self._sort_key(other)

    def __ge__(self, other: "BearingAbstract") -> bool:
        return self._sort_key(self) >= self._sort_key(other)

    def __repr__(self) -> str:
        if isinstance(self.name, (int, float)):
            name_print = str(self.name)
        else:
            name_print = repr(self.name)

        name_print = f"<{type(self).__name__}: {name_print}"
        if self.factory_type is not None:
            name_print += f", factory={self.factory_type.__name__}"
        name_print += ">"
        return name_print

    def __str__(self) -> str:
        """:returns: string value for use in Data path string"""
        raise NotImplementedError

    @staticmethod
    def _sort_key(bearing_obj: "BearingAbstract") -> Tuple[int, str, str, Any]:
        """
        Key that bearings are sorted by.

        Sorts:
            1. By class: Item, Attr, Call, [Custom Implementation by name], Bearing
            2. Bearing name type (alphabetical by class, ex: float, int, str)
            3. value of bearing name
        """
        try:
            type_value = TYPE_SORT_ORDER.index(type(bearing_obj))
        except ValueError:
            type_value = TYPE_SORT_ORDER.index("other")

        return (
            type_value,
            type(bearing_obj).__name__,
            type(bearing_obj.name).__name__,
            bearing_obj.name,
        )

    @property
    def name(self) -> "_NameType":
        """
        Read-only property.

        :return: ``name`` passed to ``__init__``.

        >>> from gemma import Attr
        >>> attribute = Attr('a')
        >>> attribute.name
        a
        """
        return self._name

    @property
    def factory_type(self) -> Optional[Type[FactoryType]]:
        """
        Read-only property.

        :return: ``factory`` passed to ``__init__``.

        >>> from gemma import Attr
        >>> attribute = Attr('a', factory=dict)
        >>> attribute.factory_type
        dict
        """
        return self._factory

    def init_factory(self) -> FactoryType:
        """
        **MAY BE IMPLEMENTED**

        Returns an initialized version of :func:`BearingAbstract.factory`.

        :return: initialized data object
        :raises TypeError: is factory is not callable

        DEFAULT IMPLEMENTATION: initializes object with no parameters.

        >>> from gemma import Attr
        >>> attribute = Attr('a', factory=dict)
        >>> attribute.init_factory()
        {}
        """
        if self.factory_type is None:
            raise TypeError("factory type is None")

        # There is a mypy bug here. This typing is correct.
        return self.factory_type()  # type: ignore

    def fetch(self, target: Any) -> Any:
        """
        **MUST BE IMPLEMENTED**

        Fetches value from target object by :func:`BearingAbstract.name`

        :param target: object to fetch value from
        :return: value to be fetched
        :raises NullNameError: generic error when bearing cannot be found
        :raises TypeError: when ``target`` is wrong type for bearing

        See documentation of the default Bearing implementations for examples:

            - :func:`Attr.fetch`
            - :func:`Item.fetch`
            - :func:`Call.fetch`
            - :func:`Fallback.fetch`
        """
        raise NotImplementedError

    def place(self, target: Any, value: Any, **kwargs: dict) -> None:
        """
        **MUST BE IMPLEMENTED**

        Sets ``value`` at :func:`BearingAbstract.name` of target object.

        :param target: target object to set value
        :param value: value to set
        :returns None: method should not return anything
        :raises NullNameError: :class:`NullNameError` should be raised if bearing
            cannot be placed
        :raises TypeError: When ``target`` is wrong type for Bearing

        See documentation of the default Bearing implementations for examples.

            - :func:`Attr.place`
            - :func:`Item.place`
            - :func:`Call.place`
            - :func:`Fallback.place`
        """
        raise NotImplementedError

    @classmethod
    def name_from_str(cls, text: str) -> Any:
        """
        **MAY BE IMPLEMENTED**

        Casts string to appropriate type for ``name`` param of ``__init__``.

        :param text: text to cast
        :return: cast value.
        :raises ValueError: if ``text`` is not cast-able.

        DEFAULT IMPLEMENTATION: Tests if the ``text`` matches to the regex pattern in
        ``BearingAbstract.REGEX``, then extracts name from pattern.

        Raises ``ValueError`` if no match.
        """
        match = re.match(cls.REGEX, text)
        if match is None:
            raise ValueError("text does not match regex")

        try:
            return match.group(1)
        except IndexError:
            return match.string

    @classmethod
    def is_compatible(cls, name: Any) -> bool:
        """
        **MAY BE IMPLEMENTED**

        Checks whether the ``name`` can be cast to current type.

        :param name: value to be cast
        :return:
            - ``True``: Can be cast.
            - ``False``: Cannot be cast

        DEFAULT IMPLEMENTATION: checks whether the type of ``name`` is in
        ``cls.NAME_TYPES``.

        Most Bearing implementations will not need to override this method, instead
        supplying a list of acceptable types to ``cls.NAME_TYPES``.

        However, some Bearings may depend on criteria other than type and override this
        method, possibly making ``cls.NAME_TYPES`` irrelevant.

        For example, a bearing used to fetch and set data from the ``dataclasses``
        module might re-implement :func:`BearingAbstract.is_compatible` as a wrapper for
        ``dataclasses.is_dataclass()``.
        """
        for kind in cls.NAME_TYPES:
            if kind is Any:
                return True
            elif isinstance(name, kind):
                return True

        return False


class Attr(BearingAbstract[str]):
    REGEX = re.compile("@(.+)")

    def __str__(self) -> str:
        return f"@{self.name}"

    def fetch(self, target: Any) -> Any:
        """
        Fetches attribute of target.

        :param target: Object to fetch attribute from
        :return: Value of attribute
        :raises NullNameError: if attribute does not exist

        Equivalent to:

        >>> getattr(target, self.name)

        Example:

        >>> from gemma import Attr
        >>> from dataclasses import dataclass
        >>>
        >>> @dataclass
        ... class Data:
        ...     a: str = 'value'
        ...
        >>> data = Data()
        >>> Attr('a').fetch(data)
        'value'

        If target does not have an attribute of bearing.name:

        >>> Attr('b').fetch(data)
        Traceback (most recent call last):
          ...
        gemma._exceptions.NullNameError: @b>
        """
        try:
            return getattr(target, self.name)
        except AttributeError:
            raise NullNameError(str(self))

    def place(self, target: Any, value: Any, **kwargs: dict) -> None:
        """
        Sets Attribute of target to ``value``.

        :param target: Object to set attribute on
        :param value: Value to set on attribute
        :return: None
        :raises NullNameError: if attribute does not exist

        Equivalent to:

        >>> setattr(target, self.name, value)

        Example, using ``data`` from the fetch example above:

        >>> data.a
        'value'
        >>> Attr('a').place(data, 'changed')
        >>> data.a
        'changed'

        If target does not have an attribute of bearing.name:

        >>> Attr('b').place(data, 'changed again')
        Traceback (most recent call last):
          ...
        gemma._exceptions.NullNameError: @b

        Unlike ``setattr()``, :func:`Attr.place` cannot be used to declare arbitrary
        attributes. Non-existent attributes will raise a NullNameError.
        """
        try:
            attr = getattr(target, self.name)
        except AttributeError:
            raise NullNameError(str(self))

        if callable(attr):
            raise TypeError(f"values set through Attr cannot be callable")

        setattr(target, self.name, value)


class Item(BearingAbstract[Any]):
    REGEX = re.compile(r"\[(.+)\]")
    NAME_TYPES = [Any]

    def __str__(self) -> str:
        return f"[{str(self.name)}]"

    def fetch(self, target: Any) -> Any:
        """
        Fetches data at index or key of ``target``

        :param target: object to fetch data from
        :return: value of index/key
        :raises NullNameError: if index/key does not exist
        :raises TypeError: if Target does not have a valid ``__getitem__`` method

        Fetch data from a list:

        >>> from gemma import Item
        >>>
        >>> data_list = ["zero", "one", "two"]
        >>> item = Item(0)
        >>> item.fetch(data_list)
        'zero'

        Fetch data from a dict:

        >>> data_dict = {"a": "a value", "b": "b value"}
        >>> item = Item("b")
        >>> item.fetch(data_dict)
        'b value'

        Fetching an Index / Item that does not exist raises :class:`NullNameError`

        >>> out_of_index = Item(5)
        >>> out_of_index.fetch(data_list)
        Traceback (most recent call last):
            ...
        gemma._exceptions.NullNameError: [5]
        >>>
        >>> bad_key = Item("c")
        >>> bad_key.fetch(data_dict)
        Traceback (most recent call last):
            ...
        gemma._exceptions.NullNameError: [c]

        An invalid name raises a :class:`NullNameError` regardless of whether
        the ``target`` object would normally raise a ``KeyError`` or ``IndexError``.

        Fetching from a ``target`` which does not support ``__getitem__`` raises a
        ``TypeError``.

        >>> no_get_item = int(1)
        >>> bad_key.fetch(no_get_item)
        Traceback (most recent call last):
            ...
        TypeError: 'int' object is not subscriptable
        """
        try:
            return target[self.name]
        except (KeyError, IndexError):
            raise NullNameError(str(self))

    def place(self, target: Any, value: Any, **kwargs: dict) -> None:
        """
        Sets ``value`` at Index/Key of ``target``

        :param target: object to set ``value`` on.
        :param value: value to set.
        :return: None
        :raises NullNameError: When Index/Key cannot be set
        :raises TypeError: When ``target`` does not support ``__setitem__``

        Changing an existing dict key:

        >>> from gemma import Item
        >>>
        >>> data_dict = {"a": "a value", "b": "b value"}
        >>> existing_item = Item("b")
        >>>
        >>> existing_item.place(data_dict, "changed")
        >>> data_dict
        {'a': 'a value', 'b': 'changed'}

        Setting a new dict key:

        >>> new_item = Item("c")
        >>> new_item.place(data_dict, "new")
        >>> data_dict
        {'a': 'a value', 'b': 'changed', 'c': 'new'}

        Changing an existing list index:

        >>> data_list = ["zero", "one", "two"]
        >>> item = Item(0)
        >>>
        >>> item.place(data_list, "changed")
        >>> data_list
        ['changed', 'one', 'two']

        Changing an index out of range does not result in :class:`NullNameError`,
        as it does with :func:`Item.fetch`.

        >>> out_of_index = Item(5)
        >>> out_of_index.place(data_list, "new value")
        >>> data_list
        ['changed', 'one', 'two', None, None, 'new value']

        ``None`` is inserted in any missing indexes between the last existing index and
        the new index.

        Attempting to place a value on a ``target`` that does not support
        ``__setitem__`` raises a ``TypeError``:

        >>> data_tuple = ("zero", "one", "two")
        >>> cannot_set = Item(0)
        >>>
        >>> cannot_set.place(data_tuple, "changed")
        Traceback (most recent call last):
          ...
        TypeError: 'tuple' object does not support item assignment

        If the object would normally raise a ``KeyError`` or ``IndexError``, it is cast
        to a :class:`NullNameError`.

        Let us create a dict class that raises a ``KeyError`` when attempting to set any
        key that is not present upon initialization:

        >>> class StrictDict(dict):
        ...     def __setitem__(self, item, value):
        ...         if not item in self:
        ...             raise KeyError
        ...         super().__setitem__(item, value)
        ...
        >>> strict = StrictDict({"a": "a value", "b": "b value"})
        >>> strict["c"] = "changed"
        Traceback (most recent call last):
            ...
        KeyError

        :class:`Item` 's place method will cast the ``KeyError`` to a
        :class:`NullNameError`.

        >>> raises_key = Item("c")
        >>> raises_key.place(strict, "changed")
        Traceback (most recent call last):
            ...
        gemma._exceptions.NullNameError: [c]
        """
        try:
            target[self.name] = value
        except KeyError:
            raise NullNameError(str(self))
        except IndexError:
            if isinstance(target, List) and isinstance(self.name, int):
                for i in range(self.name + 1 - len(target)):
                    target.append(None)
                target[self.name] = value
                return
            raise NullNameError(str(self))


class Call(BearingAbstract[str]):
    REGEX = re.compile(r"(.+?)\(\)")
    # we are going to use this to see when we need to sub out args for value
    VALUE_ARG = object()

    def __init__(
        self,
        name: str,
        func_args: Optional[Iterable] = None,
        func_kwargs: Optional[Dict[str, Any]] = None,
    ):
        """
        :param name: method name to act on
        :param func_args: ``*args`` to pass to method when fetching or placing
        :param func_kwargs: ``**kwargs`` to pass to method when fetching or placing

        Class Attributes:
            - **VALUE_ARG (** ``Any`` **):** object to act as placeholder in
              ``func_args`` and ``func_kwargs``
        """
        super().__init__(name)

        if func_args is None:
            func_args = tuple()
        else:
            func_args = tuple(func_args)

        if func_kwargs is None:
            func_kwargs = dict()

        self._func_args: tuple = func_args
        self._func_kwargs: dict = func_kwargs

    def __str__(self) -> str:
        return f"{self.name}()"

    def fetch(self, target: Any) -> Any:
        """
        Fetches value from method of ``target``

        :param target: Object to call method on.
        :return: return of method

        Getting the keys of a dict:

        >>> from gemma import Call
        >>>
        >>> data_dict = {"a": "a value", "b": "b value"}
        >>> method = Call("keys")
        >>>
        >>> method.fetch(data_dict)
        dict_keys(['a', 'b'])

        If the method does not exist, a :class:`NullNameError` is raised.

        >>> invalid_method = Call("does_not_exist")
        >>> invalid_method.fetch(data_dict)
        Traceback (most recent call last):
            ...
        gemma._exceptions.NullNameError: does_not_exist()

        When fetching a value, call will pass the ``func_args`` and ``func_kwargs``
        passed to ``__init__`` as ``*args`` and ``*kwargs``

        >>> data_list = ["repeat", "one", "two", "repeat"]
        >>> method = Call("index", func_args=("repeat", 1))
        >>> method.fetch(data_list)
        3

        This is equivalent to

        >>> data_list.index("repeat", 1)
        3
        """
        try:
            method = getattr(target, self.name)
        except AttributeError:
            raise NullNameError(str(self))

        return method(*self._func_args, **self._func_kwargs)

    def _replace_args(self, value: Any) -> Tuple[list, dict]:
        """
        Replaces CALL.VALUE in self._func_args and kwargs with ``value``.

        :param value:
        :return: (*args, *kwargs)
        """
        value_replaced = False

        kwargs = self._func_kwargs.copy()

        for key, arg in kwargs.items():
            if arg is Call.VALUE_ARG:
                kwargs[key] = value
                value_replaced = True

        args = list()

        for arg in self._func_args:
            if arg is not Call.VALUE_ARG:
                args.append(arg)
            else:
                args.append(value)
                value_replaced = True

        if not value_replaced:
            args.insert(0, value)

        return args, kwargs

    def place(self, target: Any, value: Any, **kwargs: dict) -> None:
        """
        Places value with method of ``target``.

        :param target: Object to call method on
        :param value: value to pass
        :return: None

        By default, ``value`` is passed as the first argument to the given method.

        Appending value at end of list:

        >>> from gemma import Call
        >>>
        >>> data_list = ["zero", "one", "two"]
        >>>
        >>> adds_value = Call("append")
        >>> adds_value.place(data_list, "three")
        >>>
        >>> data_list
        ['zero', 'one', 'two', 'three']

        Any additional args are passed as positional arguments, *after* ``value``. Let
        us create a list class with a method that will attempt to cast a value to a
        given type before appending it to the list:

        >>> class MultiArg(list):
        ...     def cast_append(self, value, cast_type=None):
        ...         try:
        ...             value = cast_type(value)
        ...         except (TypeError, ValueError):
        ...             pass
        ...         self.append(value)
        ...
        ...     def args_reversed(self, cast_type=None, value=None):
        ...         self.cast_append(value, cast_type)
        ...

        We can pass ``str`` to the ``cast_type`` parameter by setting it as the first
        additional argument to :class:`Call`.

        >>> data_list = MultiArg(('zero', 'one', 'two'))
        >>> data_list
        ['zero', 'one', 'two']
        >>> casts_str = Call('cast_append', func_args=(str,))
        >>> casts_str.place(data_list, 3)
        >>> data_list
        ['zero', 'one', 'two', '3']

        This is equivalent to:

        >>> data_list.cast_append(3, str)

        We can also pass ``cast_type`` as a keyword argument.

        >>> casts_str = Call('cast_append', func_kwargs={'cast_type': str})
        >>> casts_str.place(data_list, 4)
        >>> data_list
        ['zero', 'one', 'two', '3', '4']

        For most setter methods, it is likely that the value will be the first argument
        passed. However, this is not always the case. Take ``list.insert()`` -- the
        first argument is the index where the value is inserted.

        >>> data_list = ["zero", "one", "two"]
        >>> data_list.insert(0, "new")
        >>> data_list
        ['new', 'zero', 'one', 'two']

        In this case, if we want a bearing that places ``value`` at the head of a
        ``list``, we need to pass ``value`` as the *second* argument.

        We can use the ``Call.VALUE_ARG`` object to indicate that instead of being
        placed as the first argument, ``value`` should replace the ``Call.VALUE_ARG``
        whenever a new value is passed to the bearing.

        >>> data_list = ["zero", "one", "two"]
        >>>
        >>> inserts_head = Call("insert", func_args=(0, Call.VALUE_ARG))
        >>> inserts_head.place(data_list, "new")
        >>>
        >>> data_list
        ['new', 'zero', 'one', 'two']

        This also works with ``**kwarg values``. Using the ``MultiArg``, class from
        above:

        >>> data_list = MultiArg(('zero', 'one', 'two'))
        >>>
        >>> kwargs = {'value': Call.VALUE_ARG, 'cast_type': str}
        >>> inserts_head = Call("args_reversed", func_kwargs=kwargs)
        >>>
        >>> inserts_head.place(data_list, 3)
        >>> inserts_head
        ['zero', 'one', 'two', '3']
        """
        try:
            method = getattr(target, self.name)
        except AttributeError:
            raise NullNameError(str(self))

        args, kwargs = self._replace_args(value)

        method(*args, **kwargs)


_BEARING_CLASSES: List[Type[BearingAbstract]] = [Item, Call, Attr]


class Fallback(BearingAbstract[Any]):
    NAME_TYPES = [Any]
    BEARING_CLASSES: List[Type[BearingAbstract]] = _BEARING_CLASSES

    def __init__(self, name: Any):
        """
        Attempts to fetch or place data on a target using other bearing class' methods.

        :param name: name of bearing.

        **inherits from:** :class:`BearingAbstract`

        **name types:** ``Any``.

        **shorthand:** ``"name"``

        Class Attributes:
            - **BEARING_CLASSES (** ``List[Type[BearingAbstract]]`` **):** bearing
              classes to cycle through when attempting to fetch or place data.

        The available methods and order of attempts is determined by the list of types
        in ``Fallback.BEARING_CLASSES``. This makes bearing less performant than
        invoking one of its test classes directly, but does make setting up
        :class:`Course` objects easier and less tedious. The performance hit may or may
        not be worth it depending on your workflow.

        The default ``BEARING_CLASSES`` are :class:`Item`, :class:`Call`,
        and :class:`Attr`, though that can be extended by inheriting this class

        Meant as a generic class when the bearing type is not well defined in a string
        ( Allows for more compact, generic :class:`Course` declarations ).
        """
        super().__init__(name)

    def __str__(self) -> str:
        return str(self.name)

    def fetch(self, target: Any) -> Any:
        """
        Attempts to fetch data from ``target`` object.

        :param target: object to fetch data from.
        :return: value

        Cycles through the classes in ``Fallback.BEARING_CLASSES``, casting the current
        Bearing to each type, and invoking their ``fetch()`` method.

        If the cast or fetch results in a :class:``NullNameError``, ``TypeError``, or
        ``ValueError``, the exception is caught and the next class is tried.

        By default, :class:`Fallback` cycles through ``fetch()`` on :class:`Item`,
        :class:`Attr`, and :class:`Call`, in that order.

        With the default classes, if an attribute exists, it will be fetched.

        >>> from gemma import Fallback
        >>>
        >>> class TestData:
        ...     pass
        ...
        >>> test_data = TestData()
        >>> test_data.a = 'a value'
        >>>
        >>> to_fetch = Fallback('a')
        >>> to_fetch.fetch(test_data)
        'a value'

        Same with an Index.

        >>> data_dict = {"a": "a dict"}
        >>> to_fetch.fetch(data_dict)
        'a dict'

        Same with a method.

        >>> class FetchMethod:
        ...     def a(self):
        ...         return 'a method'
        ...
        >>> test_data = FetchMethod()
        >>> to_fetch.fetch(test_data)
        'a method'

        When an name has multiple compatible bearings, it takes the first method's value
        that does not throw an exception.

        >>> class TwoValid(dict):
        ...     def a(self):
        ...         return 'a method'
        ...
        >>> data_dict = TwoValid({'a': 'a item'})
        >>> to_fetch.fetch(data_dict)
        'a item'

        Both ``Item('a')`` and ``Call('a')`` would return valid values --
        ``"a method"`` and ``"a item"``, respectively -- but since :class:`Item` is
        tried first and gets a valid response, the key value is returned.
        """
        for bearing_type in self.BEARING_CLASSES:
            try:
                cast_bearing = bearing_type(self)
            except TypeError:
                continue

            try:
                return cast_bearing.fetch(target)
            except (NullNameError, TypeError, ValueError):
                pass

        raise NullNameError(repr(self))

    def place(self, target: Any, value: Any, **kwargs: dict) -> None:
        """
        Attempts to set ``value`` on ``target``.

        :param target: Object to set ``value`` on.
        :param value: Value to set.
        :return: None

        Attempts to place data on a given name of ``target`` by cycling through the
        classes in ``Fallback.BEARING_CLASSES``, casting the current Bearing to each
        type, and invoking their ``place()`` method.

        If the cast or place results in a :class:`NullNameError`, ``TypeError``, or
        ``ValueError``, the exception is caught and the next class is tried.

        By default, :class:`Fallback` cycles through ``place()`` on :class:`Item`,
        :class:`Attr`, and :class:`Call`, in that order.

        With the default classes, if an attribute exists, it will be placed.

        >>> from gemma import Fallback
        >>>
        >>> class TestData:
        ...     a = None
        ...
        >>> test_data = TestData()
        >>>
        >>> to_place = Fallback("a")
        >>> to_place.place(test_data, "a attr")
        >>>
        >>> test_data.a
        'a attr'

        Same with an Index.

        >>> data_dict = dict()
        >>> to_place.place(data_dict, "a dict")
        >>> data_dict
        {'a': 'a dict'}

        Same with a method.

        >>> class FetchMethod:
        ...     def a(self, value):
        ...         self.a = value
        ...
        >>> test_data = FetchMethod()
        >>> to_place.place(test_data, "a method")
        >>> test_data.a
        'a method'

        When an name has multiple compatible bearings, it takes the first method's value
        that does not throw an exception.

        >>> class TwoValid(dict):
        ...     def a(self, value):
        ...         self.a = value
        ...
        >>> data_dict = TwoValid()
        >>> to_place.place(data_dict, 'a value')
        >>> data_dict
        {'a': 'a value'}
        >>> data_dict.a
        <Item: 'a'>

        Both ``Item('a')`` and ``Call('a')`` would set valid values -- (to a key and
        attribute respectively) -- but since :class:`Item` is tried first and does not
        return an error, it is set to the dict's key rather than overriding
        it's ``a`` method.
        """
        for bearing_type in self.BEARING_CLASSES:
            try:
                cast_bearing = bearing_type(self)
            except TypeError:
                continue

            try:
                cast_bearing.place(target, value)
            except (NullNameError, TypeError, ValueError):
                pass
            else:
                return

        raise NullNameError(repr(self))


def _order_bearing_classes(
    bearing_classes: Optional[List[Type[BearingAbstract]]] = None,
    bearing_classes_extra: Optional[List[Type[BearingAbstract]]] = None,
) -> List[Type[BearingAbstract]]:
    """combines bearing_classes and bearing_classes_extra"""
    if bearing_classes is None:
        bearing_classes = _BEARING_CLASSES + [Fallback]
    if bearing_classes_extra is None:
        bearing_classes_extra = list()
    bearing_classes = bearing_classes_extra + bearing_classes

    return bearing_classes


def attempt_name_to_bearing(
    name: Any, bearing_type: Type[BearingAbstract]
) -> BearingAbstract:
    try:
        name = bearing_type.name_from_str(name)
        new = bearing_type(name)
    except TypeError:
        try:
            new = bearing_type(name)
        except TypeError:
            raise ValueError()
        else:
            return new
    else:
        return new


def bearing(
    name: Any,
    bearing_classes: Optional[List[Type[BearingAbstract]]] = None,
    bearing_classes_extra: Optional[List[Type[BearingAbstract]]] = None,
) -> BearingAbstract:
    """
    Factory function for bearing classes.

    :param name: value for Bearing.name
    :param bearing_classes: list and order of bearing classes to attempt casting
    :param bearing_classes_extra: additional classes to add to bearing classes. Used
        to add to defaults when ``bearing_classes`` is set to ``None``.
    :return: Bearing object

    If ``name`` is a string, bearing will attempt to cast using each class'
    :func:`BearingAbstract.from_string` method.

    Otherwise, bearing attempts to cast to each class normally, passing ``name`` as a
    single argument to each ``__init__`` method.

    The default list of classes to attempt are: :class:`Item`, :class:`Call`,
    :class:`Attr`, and :class:`Fallback` -- in that order.

    Any bearing types passed to ``bearing_classes_extra`` are put *ahead* of the
    bearings in ``bearing_classes``.

    Casting formatted strings:

    >>> from gemma import bearing
    >>>
    >>> bearing("[item_name]")
    <Item: 'item_name'>
    >>>
    >>> bearing("@attr_name")
    <Attr: 'attr_name'>
    >>>
    >>> bearing("call_name()")
    <Call: 'call_name'>

    Passing a string which does not match any of the above class' string conventions
    will result in a generic :class:`Fallback`.

    >>> bearing("unknown_name")
    <Fallback: 'unknown_name'>

    This Fallback class will be loaded with the methods of the other classes, if
    ``bearing_classes`` includes custom Bearings, those class' methods will be added
    to the list. No need to make a custom subclass to extend the pool methods available
    to :class:`Fallback` when using this factory.

    Passing a non-string will always result in an :class:`Item` object with the
    default list, since :class:`Item` accepts all types, and is attempted first.

    >>> bearing(5)
    <Item: 5>
    >>>
    >>> bearing((5, 4))
    <Item: (5, 4)>
    """
    classes_loaded = _order_bearing_classes(bearing_classes, bearing_classes_extra)

    new = None
    for this_type in classes_loaded:
        try:
            new = attempt_name_to_bearing(name, this_type)
        except ValueError:
            continue
        else:
            break

    if new is None:
        raise TypeError

    # load fallback class with class types.
    if isinstance(new, Fallback):
        classes_loaded = [x for x in classes_loaded if not issubclass(x, Fallback)]
        new.BEARING_CLASSES = classes_loaded

    return new


TYPE_SORT_ORDER: List[Union[Type[BearingAbstract], str]] = [
    Item,
    Attr,
    Call,
    "other",
    Fallback,
]
