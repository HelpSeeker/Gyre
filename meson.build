project('gyre',
  license: 'GPL-3.0-or-later',
  meson_version: '>= 0.51.0',
  version: '0.1.0',
)

# General project infos (e.g. for the about dialog)
name = 'Gyre'
domain = 'io.github.helpseeker.Gyre'
description = 'A downloader for videos from Coub'
license = 'gpl-3-0'
website = 'https://github.com/HelpSeeker/Gyre'
author = 'HelpSeeker'
email = 'AlmostSerious@protonmail.ch'
copyright = '2020'

# Dependency checks
python = import('python')
py3 = python.find_installation('python3', modules: ['aiohttp', 'gi'])
if py3.language_version().version_compare('< 3.7')
  error('Python 3.7+ required')
endif
dependency('gtk+-3.0', version: '>= 3.24')
dependency('libhandy-1', version: '>= 1.0.0')

# Paths
prefix = get_option('prefix')                       # default: /usr/local
bindir = prefix / get_option('bindir')              # default: /usr/local/bin
datadir = prefix / get_option('datadir')            # default: /usr/local/share
pkgdatadir = datadir / meson.project_name()         # default: /usr/local/share/gyre
module_dir = py3.get_install_dir()                  # default: /usr/local/lib/pythonX.Y/site-packages
desktop_file_dir = datadir / 'applications'         # default: /usr/local/share/applications
metainfo_dir = datadir / 'metainfo'                 # default: /usr/local/share/metainfo
schema_dir = datadir / 'glib-2.0' / 'schemas'       # default: /usr/local/share/glib-2.0/schemas
icon_dir = datadir / 'icons' / 'hicolor'            # default: /usr/local/share/icons/hicolor
generic_icon_dir = icon_dir / 'scalable' / 'apps'   # default: /usr/local/share/icons/hicolor/scalable/apps
symbolic_icon_dir = icon_dir / 'symbolic' / 'apps'  # default: /usr/local/share/icons/hicolor/symbolic/apps

# Install source files as Python site-package
install_subdir(meson.project_name(), install_dir: module_dir)

# Configure and install main script
conf = configuration_data()
conf.set('PYTHON', py3.path())
conf.set('MODULEDIR', module_dir)
conf.set('PKGDATADIR', pkgdatadir)
conf.set('NAME', name)
conf.set('MODULE', meson.project_name())
conf.set('DOMAIN', domain)
conf.set('COPYRIGHT', copyright)
conf.set('AUTHOR', author)
conf.set('EMAIL', email)

configure_file(
  input: meson.project_name() + '.in',
  output: meson.project_name(),
  configuration: conf,
  install: true,
  install_dir: bindir
)

subdir('data')

meson.add_install_script('build-aux' / 'meson' / 'postinstall.py')
