.. automodule:: gemma

.. _extending:

Extending gemma
===============

gemma is easily extended through subclassing. The most important class in a new
extension will almost always be a re-implementation of :class:`BearingAbstract`.
The user rarely interacts with a :class:`BearingAbstract` object directly, but it is
the building block of all other class' functionality.

See the :ref:`extension-xml` section for an example of how an extension is written.
