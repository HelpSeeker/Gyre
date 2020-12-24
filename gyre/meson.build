pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'gyre'

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', get_option('prefix') / get_option('localedir'))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'gyre.in',
  output: 'gyre',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir')
)

gyre_sources = [
  '__init__.py',
  'application.py',
  'utils.py',
]

core_sources = [
  'core' / 'container.py',
  'core' / 'coub.py',
  'core' / 'settings.py',
]

interface_sources = [
  'interface' / 'about.py',
  'interface' / 'add.py',
  'interface' / 'dialogs.py',
  'interface' / 'preferences.py',
  'interface' / 'row.py',
  'interface' / 'window.py',
]

install_data(gyre_sources, install_dir: moduledir)
install_data(core_sources, install_dir: moduledir / 'core')
install_data(interface_sources, install_dir: moduledir / 'interface')

