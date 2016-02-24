pip-faster: it's pip, just faster!
==================================
`Issues <https://github.com/yelp/pip-faster/issues>`_ |
`Github <https://github.com/yelp/pip-faster>`_ |
`PyPI <https://pypi.python.org/pypi/pip-faster/>`_

Release v\ |release| (:ref:`Installation`)

.. toctree::
   :hidden:
   :maxdepth: 2

   venv-update
   pip-faster
   internal-pypi

Introduction
------------

``pip-faster`` is an `MIT Licensed`_ tool to install your
python dependencies, a bit faster than pip does.


This project ships as two separable components: pip-faster and venv-update.

Both are designed for use on large projects with hundreds of requirements and
are used daily by Yelp_ engineers.


Why?
----

In a large application, best practice is to "pin" versions, with requirements
like ``package-x==1.2.3`` in order to ensure that dev, staging, test, and
production will all use the same code. Currently ``pip`` will always reach out
to PyPI to list the versions of ``package-x`` regardless of whether the package
is already installed, or whether its `wheel`_ can be found in the local cache.
``pip-faster`` adds these optimizations and others.

Further, generating a repeatable build of a virtualenv has many edge cases. If
a requirement is removed, it should be uninstalled when the virtualenv is
updated. If the version of python has changed, the only reliable solution is to
re-build the virtualenv from scratch. Our initial implementation would always
completely remove the virtualenv and re-build it, but this slows things down
terribly. ``venv-update`` handles all of these edge cases and more, without
completely starting from scratch (in the usual case).


`How much` faster?
------------------



``pip-faster``
--------------

pip-faster is a drop-in replacement for pip. You should find that pip-faster
gives the same results as pip, just more quickly, especially in the case of
pinned requirements (e.g. package-x==1.2.3).

If you're also using venv-update (which we heartily recommend!), you can view
pip-faster as an implementation detail. For more, see :ref:`pip-faster-details`.


.. _venv-update:

``venv-update``
---------------

A small script designed to keep a virtualenv in sync with a changing list of
requirements. Given a list of ``requirements.txt`` files, venv-update makes
sure the virtualenv state is exactly the same as if you deleted and regenerated
the virtualenv (but does so *much* more quickly).

The needs of venv-update are what drove the development of pip-faster.
For more, see :ref:`venv-update-details`.





.. _installation:

Installation
~~~~~~~~~~~~

Because ``venv-update`` is meant to be the entry-point for creating your
virtualenv_ directory and installing your packages, it's not meant to be
installed via pip; that would require a virtualenv to already exist!

Instead, the script is designed to be `vendored` (directly checked in) to your
project, and has no dependencies besides virtualenv and the standard Python
library.

.. sourcecode:: shell

 mkdir -p bin
 cd bin
 curl -O https://raw.githubusercontent.com/Yelp/pip-faster/master/venv_update.py
 mv venv_update.py venv-update
 chmod 755 venv-update
 git add venv-update
 git commit venv-update -m 'added bin/venv-update'


Usage
~~~~~

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

   [testenv]
 + venv_update =
 +     {toxinidir}/bin/venv-update \
 +        venv= {envdir} \
 +        install= -r {toxinidir}/requirements.txt -e {toxinidir}
 - deps = -rrequirements.txt
   commands =
 +     {[testenv]venv_update}
       py.test tests/
       pre-commit run --all-files

The exact changes will of course vary, but above is a general template. The
two changes are: running venv-update as the first test command, and
removing the list of ``deps`` (so that tox will never invalidate your
virtualenv itself; we want to let venv-update manage that instead).

Users of tox version <2 will want to add this as well, to avoid tox installing
all your dependencies with pip-slower:

.. sourcecode:: diff

     [tox]
     envlist = py27,py34
   + skipsdist = true


.. _MIT Licensed: https://github.com/Yelp/pip-faster/blob/master/COPYING
.. _pip: https://pip.pypa.io/en/stable/
.. _virtualenv: https://virtualenv.readthedocs.org/en/latest/
.. _wheel: https://wheel.readthedocs.org/en/latest/
.. _tox: https://tox.readthedocs.org/en/latest/
.. _yelp: https://www.yelp.com/

.. vim:textwidth=79:shiftwidth=3:noshiftround:
