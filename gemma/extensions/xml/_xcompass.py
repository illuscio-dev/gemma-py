from xml.etree.ElementTree import Element
from collections import Counter as Indexer
from typing import Union, List, Any, Tuple, Counter, Generator

from gemma import Compass, Item, Call
from ._xelm_bearing import XElm


class XCompass(Compass):
    def __init__(self, elms: Union[bool, List[str]] = True):
        super().__init__(target_types=(Element,), attrs=["text", "attrib"])
        self._elms: Union[bool, List[str]] = elms

    def item_iter(self, target: Any) -> Generator[Tuple[Item, Any], None, None]:
        """
        Now Implemented. No :class:`Item` bearings returned.
        """
        raise NotImplementedError

    def call_iter(self, target: Any) -> Generator[Tuple[Call, Any], None, None]:
        """
        Not Implemented. No :class:`Call` bearings returned.
        """
        raise NotImplementedError

    def elm_iter(self, target: Element) -> Generator[Tuple[XElm, Element], None, None]:
        """
        Yields :class:`XElm` bearing for each element on ``target``

        :param target:
        :return:
        """
        if self._elms is False:
            return
        elif isinstance(self._elms, list):
            allowed_elms = self._elms
        else:
            allowed_elms = list()

        node: Element
        count: Counter[str] = Indexer()

        for node in target:
            name = node.tag

            if allowed_elms and name not in allowed_elms:
                continue

            yield XElm((name, count[name])), node
            count[name] += 1
