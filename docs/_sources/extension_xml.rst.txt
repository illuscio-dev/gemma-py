
.. automodule:: gemma
.. automodule:: gemma.extensions.xml

.. _extension-xml:

Extension: XML
==============

The xml extension supplies classes for interacting with data from
``xml.etree.ElementTree``

Examples will share a ``root`` data object. To load, copy and paste the following: ::

    from xml.etree.ElementTree import fromstring
    
    xml_raw = (
        '<root>'
            '<a one="1" two="2"/>'
            '<b three="3" four="4">'
                '<listed>one</listed>'
                '<listed>two</listed>'
                '<listed>three</listed>'
            '</b>'
        '</root>'
    )
    root = fromstring(xml_raw)

XElm Bearing Type
-----------------

.. autoclass:: XElm
    :special-members: __init__
    :members:

XCourse
-------

Simple subclass of :class:`Course` that adds :class:`XElm` to the list of auto-cast
functions.

Like :class:`Course` / ``gemma.PORT``, :class:`XCourse` has a shorter, initialized alias
called ``XPATH``.

.. autoclass:: XCourse
    :members:

Example :func:`XCourse.fetch`
    >>> from gemma.extensions.xml import XCourse, XPath
    >>>
    >>> to_fetch = XCourse() / "<b>" / "<listed, -1>"
    >>> fetched = to_fetch.fetch(root)
    >>> fetched, fetched.text
    (<Element 'listed' at 0x10b6d7c78>, 'three')

Example :func:`XCourse.place`
    >>> to_place = XPath / "<b>" / "<listed, -1>" / "text"
    >>> to_place.place(root, "changed value")
    >>> print(tostring(root))
    b'<root>...<b four="4" three="3">...<listed>changed value</listed></b></root>'


XCompass
--------

.. autoclass:: XCompass

    Restricted compass for ``xml.etree.ElementTree.Element`` objects.

    Returns all child elements as (:class:`XElm`), value pairs.

    **Returned** :class:`Attr` **bearings:** ``.text``, ``.attrib`` by default.

    :members:

    Example
        >>> from gemma.extensions.xml import XCompass
        >>>
        >>> for this_bearing, value in XCompass().bearings_iter(root):
        ...     print(repr(this_bearing), value)
        ...
        <Attr: 'text'> None
        <Attr: 'attrib'> {}
        <XElm: ('a', 0)> <Element 'a' at 0x10b6d7ae8>
        <XElm: ('b', 0)> <Element 'b' at 0x10b6d7b88>


xsurveyor
---------

``xsurveyor`` is an instance of :class:`Surveyor` with :class:`XCompass` added to its
compasses and :class:`XCourse` as its course type.

Example
    >>> from gemma.extensions.xml import xsurveyor
    >>>
    >>> for course, value in xsurveyor.chart_iter(root):
    ...     print(repr(course), value)
    ...
    <Course: <Attr: 'text'>> None
    <Course: <Attr: 'attrib'>> {}
    <Course: <XElm: ('a', 0)>> <Element 'a' at 0x104626688>
    <Course: <XElm: ('a', 0)> / <Attr: 'text'>> None
    <Course: <XElm: ('a', 0)> / <Attr: 'attrib'>> {'one': '1', 'two': '2'}
    <Course: <XElm: ('a', 0)> / <Attr: 'attrib'> / <Item: 'one'>> 1
    <Course: <XElm: ('a', 0)> / <Attr: 'attrib'> / <Item: 'two'>> 2
    <Course: <XElm: ('b', 0)>> <Element 'b' at 0x104639f48>
    <Course: <XElm: ('b', 0)> / <Attr: 'text'>> None
    <Course: <XElm: ('b', 0)> / <Attr: 'attrib'>> {'three': '3', 'four': '4'}
    <Course: <XElm: ('b', 0)> / <Attr: 'attrib'> / <Item: 'three'>> 3
    <Course: <XElm: ('b', 0)> / <Attr: 'attrib'> / <Item: 'four'>> 4
    <Course: <XElm: ('b', 0)> / <XElm: ('listed', 0)>> <Element 'listed' at 0x104639f98>
    <Course: <XElm: ('b', 0)> / <XElm: ('listed', 0)> / <Attr: 'text'>> one
    <Course: <XElm: ('b', 0)> / <XElm: ('listed', 0)> / <Attr: 'attrib'>> {}
    <Course: <XElm: ('b', 0)> / <XElm: ('listed', 1)>> <Element 'listed' at 0x10464c638>
    <Course: <XElm: ('b', 0)> / <XElm: ('listed', 1)> / <Attr: 'text'>> two
    <Course: <XElm: ('b', 0)> / <XElm: ('listed', 1)> / <Attr: 'attrib'>> {}
    <Course: <XElm: ('b', 0)> / <XElm: ('listed', 2)>> <Element 'listed' at 0x10464c688>
    <Course: <XElm: ('b', 0)> / <XElm: ('listed', 2)> / <Attr: 'text'>> three
    <Course: <XElm: ('b', 0)> / <XElm: ('listed', 2)> / <Attr: 'attrib'>> {}


Cartography
-----------

Mapping is done through the regular :class:`Cartographer` class.

Example
    >>> from gemma import Cartographer, Coordinate
    >>> from gemma.extensions.xml import XPATH
    >>>
    ... def explode_listed(listed_elements, coord, cache):
    ...     return [x.text for x in listed_elements]
    >>>
    >>> coords = [
    ...     Coordinate(org=XPATH / "a" / "attrib" / "one", dst=XPATH / "a.one"),
    ...     Coordinate(org=XPATH / "a" / "attrib" / "two", dst=XPATH / "a.two"),
    ...     Coordinate(org=XPATH / "b" / "attrib" / "three", dst=XPATH / "b.three"),
    ...     Coordinate(org=XPATH / "b" / "attrib" / "four", dst=XPATH / "b.four"),
    ...     Coordinate(
    ...         org=XPATH / "b" / "<listed, 0:>",
    ...         dst=XPATH / "b.listed",
    ...         clean_value=explode_listed
    ...     ),
    ... ]
    >>>
    >>> destination = dict()
    >>>
    >>> Cartographer().map(root, destination, coords)
    >>> for key, value in destination.items():
    ...     print(f"{key}: {value}")
    ...
    a.one: 1
    a.two: 2
    b.three: 3
    b.four: 4
    b.listed: ['one', 'two', 'three']