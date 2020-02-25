import itertools
from ._bearings import Attr, Item, Call, BearingAbstract
from ._exceptions import NonNavigableError

from typing import (
    Mapping,
    Any,
    Type,
    Union,
    List,
    Generator,
    Iterable,
    Tuple,
    Sequence,
    Optional,
    Callable,
)


class Compass:
    _BEARING_ITER_METHODS: List[Callable] = list()
    _BEARING_ITER_CLASS: str = ""

    def __new__(cls, *args: Iterable, **kwargs: dict) -> "Compass":
        new_compass = object.__new__(cls)

        # lets stash the classes bearing discovery methods so we don't need to discover
        # them every time we call .bearings_iter().

        # first we check if this subclass has already stashed its methods, if it has
        # we can skip over the step
        if cls._BEARING_ITER_CLASS == cls.__name__:
            return new_compass

        # otherwise, lets iter through the current dir() and find them.
        methods = list()

        for name in dir(cls):
            if name == "bearings_iter":
                continue
            if not name.endswith("_iter"):
                continue

            item = getattr(cls, name)
            methods.append(item)

        # we stash the methods and the name of the class who stashed them here, so we
        # don't have to do it the next time this implementation is initiated.
        cls._BEARING_ITER_METHODS = methods
        cls._BEARING_ITER_CLASS = cls.__name__

        return new_compass

    def __init__(
        self,
        target_types: Optional[Union[Tuple[Type, ...], Type]] = None,
        attrs: Union[bool, List[str]] = True,
        items: Union[bool, List[Any]] = True,
        calls: Union[bool, List[str]] = False,
    ):
        """
        Contains rules for how to map a type's bearings:

            - what bearings should be available when mapping.
            - what type of bearing should be returned.

        :param target_types: The classes of object that this compass can map.

            - ``NoneType`` = all objects accepted.

        :param attrs: Restricted list of :class:`Attr` ``name`` values the compass can
            return.

            - ``True``: return all :class:`Attr` bearings (default).
            - ``False``: return no :class:`Attr` bearings.

        :param items: Restricted list of :class:`Item` ``name`` values the compass can
            return.

            - ``True``: return all :class:`Item` bearings (default).
            - ``False``: return no :class:`Item` bearings.

        :param calls: Restricted list of :class:`Call` ``name`` values the compass can
            return.

            - ``True``: return all :class:`Call` bearings.
            - ``False``: return no :class:`Call` bearings (default).

        The core use of the Compass object is through :func:`Compass.bearings_iter`.
        """

        self._target_types: Optional[Union[Tuple[Type, ...], Type]] = target_types
        self._attrs: Union[bool, List[str]] = attrs
        self._items: Union[bool, List[Any]] = items
        self._calls: Union[bool, List[str]] = calls

    def bearings_iter(
        self, target: Any
    ) -> Generator[Tuple[BearingAbstract, Any], None, None]:
        """
        Yields all bearing names of ``target`` as :class:`BearingAbstract`
        objects.

        :param target: target to yield bearings of
        :return: (bearing, value) pair for each valid bearing in ``target``

        :raises NonNavigableError: If ``target`` type cannot be inspected by Compass.

        Bearings are not yielded in sorted order. Values are yielded from all other
        methods ending in ``_iter``. For the default :class:`Compass`, these methods are
        :func:`Compass.attr_iter`, :func:`Compass.item_iter`,
        and :func:`Compass.call_iter`. Any method that raises ``NotImplementedError``
        is skipped silently.

        Compasses are used to help :class:`Surveyor` objects traverse through a data
        structure. Compasses tell surveyors what bearings it should
        traverse for a given object type.

        See main :class:`Compass` documentation for examples.
        """
        if not self.is_navigable(target):
            raise NonNavigableError(f"{type(self).__name__} cannot map {repr(target)}")

        # Iterate through the bearing methods and yield their results.
        for method in self._BEARING_ITER_METHODS:
            try:
                yield from method(self, target)
            except NotImplementedError:
                pass

    def bearings(self, target: Any) -> List[Tuple[BearingAbstract, Any]]:
        """
        Returns all results from :func:`Compass.bearings_iter` as ``list``.

        :param target: object to get bearings of
        :return: List of (bearing, value) pairs.

        ``list`` will not be sorted.
        """
        return [x for x in self.bearings_iter(target)]

    def attr_iter(self, target: Any) -> Generator[Tuple[Attr, Any], None, None]:
        """
        Yields (:class:`Attr`, value) pairs for attributes of ``target``.

        :param target: object to return attributes of.

        :return: (Attr, value) pair of next valid attr on ``target``
        :raises StopIteration: At end.

        Custom compass should raise ``NotImplementedError`` if functionality to be
        disabled.

        This method is not meant to be called directly, but through
        :func:`Compass.bearings_iter`
        """
        attr_names: Iterable[str] = list()

        if self._attrs is True:
            try:
                attr_names = (x for x in target.__dict__ if not x.startswith("_"))
            except AttributeError:
                try:
                    attr_names = (x for x in target.__slots__ if not x.startswith("_"))
                except AttributeError:
                    attr_names = list()
        elif isinstance(self._attrs, list):
            attr_names = self._attrs

        for attr in attr_names:
            yield Attr(attr), getattr(target, attr)

    def item_iter(self, target: Any) -> Generator[Tuple[Item, Any], None, None]:
        """
        Yields (:class:`Item`, value) pairs for keys/indexes of ``target``.

        :param target: object to return item names of.

        :return: (item name, value) of next valid key/index on ``target``
        :raises StopIteration: At end.

        Custom compass should raise ``NotImplementedError`` if functionality to be
        disabled.

        This method is not meant to be called directly, but through
        :func:`Compass.bearings_iter`
        """
        coordinates: Iterable[Tuple[Any, Any]] = list()
        item_names: Iterable[Any] = list()

        if isinstance(self._items, list):
            item_names = self._items

        if self._items is False:
            pass
        elif isinstance(target, Mapping):
            coordinates = (x for x in target.items())
        elif isinstance(target, Sequence):
            coordinates = zip(itertools.count(0), (x for x in target))

        for item, value in coordinates:
            if self._items is True or item in item_names:
                yield Item(item), value

    def call_iter(self, target: Any) -> Generator[Tuple[Call, Any], None, None]:
        """
        Yields (:class:`Call`, value) pairs for methods of ``target``.

        :param target: object to return item names of.

        :return: (method name as bearing, value) of next valid method on ``target``
        :raises StopIteration: At end.

        Custom compass should raise ``NotImplementedError`` if functionality to be
        disabled.

        This method is not meant to be called directly, but through
        :func:`Compass.bearings_iter`
        """
        if self._calls is False:
            return

        methods = (x for x in type(target).__dict__.keys())

        for method_name in methods:
            method_function = getattr(target, method_name)

            if not callable(method_function):
                continue
            if self._calls is True and method_name.startswith("_"):
                continue
            elif isinstance(self._calls, list) and method_name not in self._calls:
                continue

            yield Call(method_name), method_function()

    def is_navigable(self, target: Any) -> bool:
        """
        Whether the compass can provide Bearings for ``target``.

        :param target: Object to check
        :return:
            - ``True``: compass can provide Bearings for target.
            - ``False``: Cannot.

        Can be overridden for custom inspection.

        DEFAULT BEHAVIOR: compares the type of ``target`` to ``target_types``
        passed to ``__init__`` using ``isinstance()``

        If the ``target_types`` param was ``None`` or the ``target`` type passes,
        ``True`` is returned.
        """
        if self._target_types is None:
            return True
        if isinstance(target, self._target_types):
            return True
        else:
            return False
