#!/bin/bash
set -Eeu
trap 'echo "[31mFAILED[m (code $?)"' ERR

colorize() {
    echo "[01;36m>[m [01;33m$@[m" >&2
    "$@"
}
canhas(){
    command -v "$1" >/dev/null
}
download() {
    if canhas curl; then
        colorize curl "$1" --output "$2"
    elif canhas wget; then
        colorize wget "$1" --output-document "$2"
    else
        echo "Could not find 'curl', nor 'wget'."
        exit 1
    fi
}

colorize mkdir -p ./bin
download https://github.com/Yelp/venv-update/raw/stable/venv_update.py bin/venv-update
colorize chmod 755 bin/venv-update

echo '
I have just installed `venv-update` to your bin/ directory.
You should commit it to your source control.

To install python requirements from ./requirements.txt to ./venv/,
simply run: 

    ./bin/venv-update

Please see the user documentation at:
    http://venv-update.rtfd.org/en/stable/
'
