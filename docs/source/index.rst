venv-update: quick, exact
=========================
`Issues <https://github.com/yelp/pip-faster/issues>`_ |
`Github <https://github.com/yelp/pip-faster>`_ |
`CI <https://travis-ci.org/Yelp/venv-update>`_ |
`PyPI <https://pypi.python.org/pypi/pip-faster/>`_

Release v\ |release| (:ref:`Installation`)

.. toctree::
   :hidden:

   Documentation overview <self>
   venv-update
   pip-faster

Introduction
------------

venv-update is an `MIT-Licensed`_ tool to quickly and exactly synchronize
a large python project's virtualenv with its `requirements`_.

This project ships as two separable components: ``pip-faster`` and
``venv-update``.

Both are designed for use on large projects with hundreds of requirements and
are used daily by Yelp_ engineers.


Why?
----

Generating a repeatable build of a virtualenv has many edge cases. If
a requirement is removed, it should be uninstalled when the virtualenv is
updated. If the version of python has changed, the only reliable solution is to
re-build the virtualenv from scratch. Initially, this was exactly how we
implemented updates of our virtualenv, but it slowed things down terribly.
``venv-update`` handles all of these edge cases and more, without completely
starting from scratch (in the usual case).

In a large application, best practice is to "pin" versions, with requirements
like ``package-x==1.2.3`` in order to ensure that dev, staging, test, and
production will all use the same code. Currently ``pip`` will always reach out
to PyPI to list the versions of ``package-x`` regardless of whether the package
is already installed, or whether its `wheel`_ can be found in the local cache.
``pip-faster`` adds these optimizations and others.


.. _venv-update:

``venv-update``
---------------

A small script designed to keep a virtualenv in sync with a changing list of
requirements. The contract of ``venv-update`` is this:

   The virtualenv state will be exactly the same as if you deleted and rebuilt
   it from scratch, but will get there in *much* less time.

The needs of venv-update are what drove the development of pip-faster.
For more, see :ref:`venv-update-details`.


``pip-faster``
--------------

pip-faster is a drop-in replacement for pip. ``pip-faster``'s contract is:

   Take the same argumeents and give the same results as ``pip``, just more quickly.

This is *especially* true in the case of pinned requirements (e.g. ``package-x==1.2.3``).
If you're also using venv-update (which we heartily recommend!), you can view
pip-faster as an implementation detail. For more, see :ref:`pip-faster-details`.


`How much` faster?
~~~~~~~~~~~~~~~~~~


If we install `plone`_ (a large python application with more than 250
dependencies) we get these numbers:

+---------+--------------+--------------+---------------+
| testcase|  pip v8.0.2  |  pip-faster  |  improvement  |
+=========+==============+==============+===============+
| cold    |   4m 39s     |    4m 16s    |       8%      |
+---------+--------------+--------------+---------------+
| noop    |    7.11s     |     2.40s    |    **196%**   |
+---------+--------------+--------------+---------------+
| warm    |    44.6s     |     21.3s    |    **109%**   |
+---------+--------------+--------------+---------------+

In the "cold" case, all caches are completely empty.
In the "noop" case nothing needs to be done in order to update the
virtualenv.
In the "warm" case caches are fully populated, but the virtualenv has been
completely deleted.

The :ref:`benchmarks` page has more detail.


.. _installation:

Installation
------------

Because ``venv-update`` is meant to be the entry-point for creating your
virtualenv_ directory and installing your packages, it's not meant to be
installed via pip; that would require a virtualenv to already exist!

Instead, the script is designed to be `vendored` (directly checked in) to your
project. It has no dependencies other than `virtualenv`_ and the standard
Python library.


.. parsed-literal::

 curl -o venv-update `<https://raw.githubusercontent.com/Yelp/venv-update/v2.1.1/venv_update.py>`_
 chmod +x venv-update


Usage
------------

By default, running ``venv-update`` will create a virtualenv named ``venv`` in the
current directory, using ``requirements.txt`` in the current directory. This
should be the desired default for most projects.

If you need more control, you can pass additional options to both
``virtualenv`` and ``pip``. The command-line help gives more detail:

.. automodule:: venv_update

... in your ``Makefile``
~~~~~~~~~~~~~~~~~~~~~~~~

venv-update is a good fit for use with make because it is idempotent and should
never fail, under normal circumstances. Here's an example Makefile:

.. sourcecode:: make

 venv: requirements.txt
    ./bin/venv-update

 .PHONY: run-some-script
 run-some-script: venv
    ./venv/bin/some-script


... with tox
~~~~~~~~~~~~

tox_ is a useful tool for testing libraries against multiple versions of
the Python interpreter. You can speed it up by telling it to use venv-update
for dependency installation; not only will it avoid network access and prefer
wheels, but it's also better at syncing a virtualenv (whereas tox will often
throw out an entire virtualenv and start over).

To start using venv-update inside tox, copy the venv-update script into
your project (for example, at ``bin/venv-update``).

Then, apply a change like this to your ``tox.ini`` file:

.. sourcecode:: diff


   [tox]
   envlist = py27,py34
 + skipsdist = true

   [testenv]
 + venv_update =
 +     {toxinidir}/bin/venv-update \
 +        venv= {envdir} \
 +        install= -r {toxinidir}/requirements.txt {toxinidir}
 - deps = -rrequirements.txt
   commands =
 +     {[testenv]venv_update}
       py.test tests/
       pre-commit run --all-files

The exact changes will of course vary, but above is a general template. The
two changes are: running venv-update as the first test command, and
removing the list of ``deps`` (so that tox will never invalidate your
virtualenv itself; we want to let venv-update manage that instead).
The ``skipsdist`` avoids installing your package twice. In tox<2, it also
prevents all of your packages dependencies from being installed by pip-slower.


.. _MIT-Licensed: https://github.com/Yelp/pip-faster/blob/latest/COPYING
.. _requirements: https://pip.pypa.io/en/stable/user_guide/#requirements-files
.. _plone: https://en.wikipedia.org/wiki/Plone_(software)
.. _pip: https://pip.pypa.io/en/stable/
.. _virtualenv: https://virtualenv.readthedocs.org/en/latest/
.. _wheel: https://wheel.readthedocs.org/en/latest/
.. _tox: https://tox.readthedocs.org/en/latest/
.. _yelp: https://www.yelp.com/

.. vim:textwidth=79:shiftwidth=3:noshiftround:
