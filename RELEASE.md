**NOTE:** This guide is only useful for the owners of the pip-faster project.

If the version still needs to be bumped:

1. `git checkout upstream/stable -b {{branch}}`
1. bump `venv_update.py`
1. `git commit -m "this is {{version}}"`
1. Create a pull request
1. Wait for review / merge


When the version has been bumped:

1. `make release`
