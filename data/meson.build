# Configure, validate and install desktop file
desktop_conf = configuration_data()
desktop_conf.set('NAME', name)
desktop_conf.set('DESCRIPTION', description)
desktop_conf.set('EXEC', meson.project_name())
desktop_conf.set('DOMAIN', domain)

desktop_file = configure_file(
  input: domain + '.desktop.in',
  output: domain + '.desktop',
  configuration: desktop_conf,
)

desktop_util = find_program('desktop-file-validate', required: false)
if desktop_util.found()
  test('Test desktop file', desktop_util, args: [desktop_file])
endif

install_data(desktop_file, install_dir: desktop_file_dir)

# Configure, validate and install metainfo file (aka appdata)
metainfo_conf = configuration_data()
metainfo_conf.set('COPYRIGHT', copyright)
metainfo_conf.set('AUTHOR', author)
metainfo_conf.set('EMAIL', email)
metainfo_conf.set('DOMAIN', domain)
metainfo_conf.set('LICENSE', meson.project_license()[0])
metainfo_conf.set('NAME', name)
metainfo_conf.set('DESCRIPTION', description)
metainfo_conf.set('WEBSITE', website)

metainfo = configure_file(
  input: domain + '.metainfo.xml.in',
  output: domain + '.metainfo.xml',
  configuration: metainfo_conf,
)

metainfo_util = find_program('appstream-util', required: false)
if metainfo_util.found()
  test('Test metainfo', metainfo_util, args: ['validate', metainfo])
endif

install_data(metainfo, install_dir: metainfo_dir)

# Install and validate gsettings schema
schema_conf = configuration_data()
schema_conf.set('DOMAIN', domain)
schema_conf.set('PATH', '/'.join(domain.split('.')))

schema = configure_file(
  input: domain + '.gschema.xml.in',
  output: domain + '.gschema.xml',
  configuration: schema_conf,
)

glib_compile = find_program('glib-compile-schemas', required: false)
if glib_compile.found()
  test('Test schema', glib_compile, args: ['--strict', '--dry-run', meson.current_source_dir()])
endif

install_data(schema, install_dir: schema_dir)

# Configure about dialog UI file (final configuration done during gresource compiling)
about_conf = configuration_data()
about_conf.set('NAME', name)
about_conf.set('VERSION', meson.project_version())
about_conf.set('DOMAIN', domain)
about_conf.set('DESCRIPTION', description)
about_conf.set('LICENSE', license)
about_conf.set('WEBSITE', website)
about_conf.set('AUTHOR', author)
about_conf.set('COPYRIGHT', copyright)

# Compile and install gresource file
gnome = import('gnome')
gnome.compile_resources(domain,
  domain + '.gresource.xml',
  gresource_bundle: true,
  dependencies: configure_file(
      input: 'ui' / 'about.ui.in',
      output: 'about.ui',
      configuration: about_conf
  ),
  install: true,
  install_dir: pkgdatadir,
)

subdir('icons')
