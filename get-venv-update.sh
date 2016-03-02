#!/bin/sh
set -eu

mkdir -p ./bin
curl --silent https://raw.githubusercontent.com/Yelp/venv-update/development/venv_update.py --output bin/venv-update
chmod 755 bin/venv-update

echo 'Oh, hi!
I have installed `venv-update` to your bin/ directory.
You should commit it to your source control.

To install python requirements from ./requirements.txt to ./venv/,
simply run: 

    ./bin/venv-update

Please see the user documentation at:
    http://venv-update.rtfd.org/en/stable/
'
