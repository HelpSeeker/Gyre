pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
desktopfiledir = get_option('datadir') / 'applications'
appdatadir = get_option('datadir') / 'metainfo'
schemadir = get_option('datadir') / 'glib-2.0' / 'schemas'
icondir = get_option('datadir') / 'icons' / 'hicolor'

desktopfile = 'io.github.helpseeker.Gyre.desktop'
appdata = 'io.github.helpseeker.Gyre.metainfo.xml'
schema = 'io.github.helpseeker.Gyre.gschema.xml'
appicon = 'icons' / 'io.github.helpseeker.Gyre.svg'
symbolicicon = 'icons' / 'io.github.helpseeker.Gyre-symbolic.svg'

gnome = import('gnome')

# Gresources
gnome.compile_resources('gyre',
  'gyre.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
)

# Desktop file
install_data(desktopfile, install_dir: desktopfiledir)

desktop_utils = find_program('desktop-file-validate', required: false)
if desktop_utils.found()
  test('Validate desktop file', desktop_utils,
    args: [desktopfiledir / desktopfile]
  )
endif

# Appdata
install_data(appdata, install_dir: appdatadir)

appstream_util = find_program('appstream-util', required: false)
if appstream_util.found()
  test('Validate appstream file', appstream_util,
    args: ['validate-relax', appdatadir / appdata]
  )
endif

# GSettings schema
install_data(schema, install_dir: schemadir)

compile_schemas = find_program('glib-compile-schemas', required: false)
if compile_schemas.found()
  test('Validate schema file', compile_schemas,
    args: ['--strict', '--dry-run', meson.current_source_dir()]
  )
endif

# Icons
install_data(appicon, install_dir: icondir / 'scalable' / 'apps')
install_data(symbolicicon, install_dir: icondir / 'symbolic' / 'apps')
