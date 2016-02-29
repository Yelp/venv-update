**NOTE:** This guide is only useful for the owners of the pip-faster project.

1. `git checkout upstream/stable -b {{branch}}`
1. bump `venv_update.py`
1. `git commit -m "this is {{version}}"`
1. Create a pull request
1. Wait for review / merge
1. go to https://github.com/Yelp/pip-faster/releases and add a tag
1. `git fetch yelp --tags`
1. `git checkout v1.1.0`   --  for example
1.  upload to pypi
    1. if you need to set up pypy auth, `python setup.py register` and follow the prompts
    1. `python setup.py sdist bdist_wheel`
    1. `twine upload --skip-existing dist/*`
1. `fetch_python_package pip-faster` -- upload to pypi.yelpcorp
