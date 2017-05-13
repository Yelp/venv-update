**NOTE:** This guide is only useful for the owners of the venv-update project.

1. start on the latest master
1. bump `venv_update.py`
1. bump the URL in the `docs/source/index.rst` curl command with the new
   version tag
1. `git commit -m "this is {{version}}"`
1. `git tag v{{version}}`
1. `git push origin master --tags`
1.  upload to pypi
    1. if you need to set up pypy auth, `python setup.py register` and follow the prompts
    1. `python setup.py sdist bdist_wheel`
    1. `twine upload --skip-existing dist/*`
1. `fetch-python-package venv-update` -- upload to pypi.yelpcorp
