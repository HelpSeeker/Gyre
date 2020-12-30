#!/bin/sh

if [ "$0" != "./test.sh" ]; then
    echo "Don't run test.sh from outside the source directory!"
    exit
fi

build="$(pwd)/test_build"
install="$(pwd)/test_install"

meson setup --prefix="$install" "$build" .
cd "$build"
meson test || exit
ninja install

GSETTINGS_SCHEMA_DIR="$install/share/glib-2.0/schemas" "$install/bin/gyre"

