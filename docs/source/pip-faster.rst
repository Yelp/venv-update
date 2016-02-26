.. _pip-faster-details:

``pip-faster`` in detail
========================


By design ``pip-faster`` maintains the interface of pip, and should only have a
few desirable behavior differences, listed below.

#. ``pip-faster`` adds optional "prune" capability to the ``pip install``
   subcommand.  ``pip-faster install --prune`` will *uninstall* any installed
   packages that are not required (as arguments to the same install command).
   This is used by default in :ref:`venv-update` to implement reproducible builds.

#. We've taken great care to reduce the number of round-trips to PyPI, which
   makes up the majority of time spent on what should be a no-op update. For
   example, if you're installing a specific version of a package which we
   already have cached, there's no need to talk to PyPI, but vanilla pip will.

#. Packages are downloaded and `wheeled`_ before installation (if they
   aren't available from PyPI as wheels). If the virtualenv needs to be rebuilt,
   or you use the same requirement in another project, the wheel can be reused.
   This greatly speeds up installation of projects like lxml or numpy which have
   a slow-to-compile binary component.

   Mainline pip recently added this feature (in pip 7.0, 2015-05-21). We plan
   to merge, but this isn't currently an urgent work item; all of our use cases
   are satisfied. However, patches `are` welcome.

#. ``pip-faster`` will refuse to install package versions which conflict (we
   generally consider this a feature); stock pip, on the other hand, will
   happily install conflicting packages. Similarly, pip-faster detects circular
   dependencies and unsatisfied dependencies and throws an error where stock
   pip would not.


Installation
~~~~~~~~~~~~

You can ``pip install venv-update`` to get ``pip-faster``, the same way you
would any other Python tool, but if you're using :ref:`venv-update` it's not
necessary to install pip-faster; the venv-update script will install the
correct version inside your virtualenv for you.


.. _wheeled: https://wheel.readthedocs.org/en/latest/




.. toctree::
   internal-pypi
   benchmarks

.. vim:textwidth=79:sts=3:shiftwidth=3:noshiftround:
