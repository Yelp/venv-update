.. _venv-update-details:

``venv-update`` in detail
=========================

venv-update is a small script whose job is to idempotently ensure the existence
and correctness of a project's virtualenv, and synchronize it with its
requirements.

We like to call venv-update from our Makefiles to create and maintain a
virtualenv. It does the following:

* Ensures a virtualenv exists at the specified location with the specified
  Python version, and that it is valid. It will create or recreate a virtualenv
  as necessary to ensure that one venv-update invocation is all that's needed.

* Calculates the difference in packages derived from the ``requirements.txt``
  files and the installed packages. Packages will be uninstalled, upgraded, or
  installed as necessary.

  The goal is that venv-update will put you in the same state as if you wipe
  away your virtualenv and rebuild it with ``pip install``, but much more
  quickly.

* Takes advantage of ``pip-faster`` for package installation (see below) to
  avoid network access and rebuilding packages as much as possible.

For reference, a project with 250 dependencies which are all pinned can run a
no-op venv-update in ~2 seconds with no network access. The running time when
changes are needed is dominated by the time it takes to download and install
packages, but is generally quite fast (on the order of ~10 seconds).


Customizing the install command
-------------------------------

If you don't like pip-faster, for whatever reason, ``venv-update`` provides
sufficient control to use "plain-old" pip, or any other command for that
matter.

In order to tell venv-update to install pip, rather than pip-faster::

   echo 'pip>8' > requirements.d/venv-update.txt


To tell venv-update to `run` pip rather than pip-faster::

   venv-update install-command= pip install --upgrade

.. vim:textwidth=79:shiftwidth=3:noshiftround:
