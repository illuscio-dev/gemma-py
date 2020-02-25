import re
from typing import Tuple, Union, Optional, Type, Pattern, Any, List
from xml.etree.ElementTree import Element

from gemma import BearingAbstract, NullNameError, bearing
from gemma.extensions.typing import FactoryType


class XElm(BearingAbstract[Tuple[str, Union[int, slice]]]):
    REGEX: Pattern = re.compile(r"<(.+)>")
    NAME_TYPES = [tuple, str]

    def __init__(
        self,
        name: Union[str, Tuple[str, Union[int, slice]], BearingAbstract],
        factory: Optional[Type[FactoryType]] = None,
    ):
        """
        Fetches and places ``xml.etree.ElementTree.Element`` objects from / on parent
        Elements.

        :param name: tag name, index of Element
        :param factory: Type for filling empty bearings during a place.
        """
        name_cast: Tuple[str, Union[int, slice]]

        if isinstance(name, str):
            name_cast = name, 0
        elif isinstance(name, BearingAbstract):
            name_cast = name.name, 0
        else:
            name_cast = name

        if not isinstance(name_cast[1], (int, slice)):
            raise TypeError("index of name must me int or slice")

        super().__init__(name_cast, factory)

    def __str__(self) -> str:
        return f"<{self.tag}, {self.index}>"

    @property
    def tag(self) -> str:
        """
        :return: tag name of element
        """
        return self.name[0]

    @property
    def index(self) -> Union[int, slice]:
        """
        :return: index of element (defaults to "0")
        """
        if isinstance(self.name, tuple):
            return self.name[1]

    def fetch(self, target: Element) -> Union[Element, List[Element]]:
        """
        Fetches ``xml.etree.ElementTree.Element`` from ``target``

        :param target: ``Element`` to fetch from.

        :returns: ``Element with matching name``

        Equivalent to ``target.findall(self.tag)[self.index]``

        Example:
            >>> elm_fetcher = XElm("a")
            >>> fetched = elm_fetcher.fetch(root)
            >>> fetched.tag
            'a'
            >>> fetched.attrib
            {'one': '1', 'two': '2'}
        """
        # need this here for when fallback is testing fetch methods
        if not isinstance(target, Element):
            raise NullNameError(f"{target} is not xml element")

        if self.index == 0:
            element = target.find(self.tag)
            if element is None:
                raise self._null_name_error()
            return element
        else:
            element_list = target.findall(self.tag)
            try:
                return element_list[self.index]
            except IndexError:
                raise self._null_name_error()

    def place(self, target: Element, value: Element, **kwargs: dict) -> None:
        """
        Inserts ``value`` on ``target``

        :param target: ``Element`` to fetch from.
        :param value: to insert

        :returns: None

        Equivalent to ``target.insert(self.index, self.tag)``

        Example:
            >>> elm_placer = XElm(("b", 0))
            >>> elm_placer.place(root, Element("new node"))
            >>> from xml.etree.ElementTree import tostring
            >>> print(tostring(root))
            '<root>...<b four="4" three="3">/...<new node /></root>'
        """
        # need this here for when fallback is testing place methods
        if not isinstance(target, Element):
            raise NullNameError(f"target is not xml element: {target}")

        if not isinstance(value, Element):
            raise NullNameError(f"value is not xml element: {value}")

        try:
            kwargs["place_factory"]
        except KeyError:
            pass
        else:
            target.insert(-1, value)
            return

        target_element = self.fetch(target)
        target_element.insert(-1, value)

    @classmethod
    def name_from_str(cls, text: str) -> Tuple[str, Union[int, slice]]:
        """
        Tag and index (if present).

        :param text: text to be converted
        :return: name, index

        Allowed conventions:

            - <name>
            - <name, 0>
            - <name, 1:4>

        If no index is passed, ``0`` will be assumed.
        """
        name: str = super().name_from_str(text)

        try:
            name, index = name.split(",")
        except ValueError:
            return name, 0

        name = name.strip(" ")
        index = index.strip(" ")

        try:
            this_slice = _string_to_slice(index)
        except ValueError:
            return name, int(index)
        else:
            return name, this_slice

    def init_factory(self) -> FactoryType:
        """
        As :func:`BearingAbstract.init_factory`, but will return xml elements
        with :func:`BearingAbstract.name` loaded as tag name.

        :return: initialized type.
        """
        if self.factory_type is None:
            raise TypeError()
        if issubclass(self.factory_type, Element):
            # mypy is complaining here even though this is a valid return type.
            return self.factory_type(self.tag)  # type: ignore
        else:
            return super().init_factory()

    def _null_name_error(self) -> NullNameError:
        """pre-loaded NullNameError with message"""
        return NullNameError(f"could not find index {self.index} for tag {self.tag}")


def _string_to_slice(text: str) -> slice:

    slice1, slice2 = text.split(":")

    slice1 = slice1.strip(" ")
    slice2 = slice2.strip(" ")

    if not slice1:
        slice1_int = None
    else:
        slice1_int = int(slice1)

    if not slice2:
        slice2_int = None
    else:
        slice2_int = int(slice2)

    return slice(slice1_int, slice2_int)


def xbearing(
    name: Any,
    bearing_classes: Optional[List[Type[BearingAbstract]]] = None,
    bearing_classes_extra: Optional[List[Type[BearingAbstract]]] = None,
) -> BearingAbstract:
    """
    As :func:`bearing`, but inserts :class:`XElm` at head of
    ``bearing_classes_extra``
    """
    if bearing_classes_extra is None:
        bearing_classes_extra = list()

    if XElm not in bearing_classes_extra:
        bearing_classes_extra.insert(0, XElm)
    return bearing(
        name,
        bearing_classes=bearing_classes,
        bearing_classes_extra=bearing_classes_extra,
    )
