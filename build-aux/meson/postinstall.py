#!/usr/bin/env python3

import os
from subprocess import call

prefix = os.environ.get('MESON_INSTALL_PREFIX', '/usr/local')
datadir = os.path.join(prefix, 'share')
destdir = os.environ.get('DESTDIR', '')

# Assume msys2 (mingw64) environment on Windows
if os.name == "nt":
    print('Updating icon cache...')
    call(['gtk-update-icon-cache-3.0.exe', '-qtf', os.path.join(datadir, 'icons', 'hicolor')])

    print('Compiling GSettings schemas...')
    call(['glib-compile-schemas.exe', os.path.join(datadir, 'glib-2.0', 'schemas')])
# Package managers set this so we don't need to run
elif not destdir:
    print('Updating icon cache...')
    call(['gtk-update-icon-cache', '-qtf', os.path.join(datadir, 'icons', 'hicolor')])

    print('Updating desktop database...')
    call(['update-desktop-database', '-q', os.path.join(datadir, 'applications')])

    print('Compiling GSettings schemas...')
    call(['glib-compile-schemas', os.path.join(datadir, 'glib-2.0', 'schemas')])
