project('gyre',  
          version: '0.1.0',
    meson_version: '>= 0.50.0',
  default_options: [ 'warning_level=2',
                   ],
)

dependency('libhandy-1', version: '>= 1.0.0')

subdir('data')
subdir('gyre')

meson.add_install_script('build-aux/meson/postinstall.py')
