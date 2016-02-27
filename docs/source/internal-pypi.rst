Internal PyPI Servers
---------------------

Under linux, performance will be much better if you use an internal PyPI server
instead of the `public PyPI`_.

Besides the potentially lesser latency, an internal PyPI server allows for
uploading binary wheels compiled for Linux. Unlike OS X or Windows, installing
projects like lxml on Linux is normally extremely slow since they will need to
be compiled during every installation.

pip-faster improves this by only compiling on the first installation for each
user (this is also the default behavior for pip >= 7), but this doesn't help
for the first run.

Using an internal PyPI server which allows uploading of Linux wheels can
improve speed greatly. Unfortunately, these wheels are guaranteed compatible
only with the same Linux distribution they were compiled on, so this only works
if your developers work in very homogeneous environments.

For both venv-update and pip-faster, you can specify an index server by setting
the ``$PIP_INDEX_URL`` environment variable (or ``$PIP_EXTRA_INDEX_URL`` if you
want to supplement but not replace the default PyPI). For pip-faster you can
also use ``-i`` or ``-e``, just like in regular pip.


.. _public PyPI: https://pypi.python.org/pypi
