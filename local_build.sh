#!/bin/sh

meson . _build
cd _build
meson configure -Dprefix=$(pwd)/testdir
ninja install

GSETTINGS_SCHEMA_DIR=testdir/share/glib-2.0/schemas ./testdir/bin/gyre

