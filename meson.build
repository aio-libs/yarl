project(
    'yarl',
    'c',
    default_options: ['buildtype=release'],
    meson_version: '>= 1.3.0',
)

py_inter = import('python').find_installation()

PY_IMPL = run_command(
    py_inter,
    '-c',
    'import sys; print(sys.implementation.name)',
    check: true,
).stdout().strip()

# meson really don't like environment and it doesn't provide a API to get them.
# So we will need to use python command to get env
skip_env = run_command(
    py_inter,
    '-c',
    'import os; print(os.environ.get("YARL_NO_EXTENSIONS", ""))',
    check: true,
).stdout().strip()

pure_py = (get_option('pure-python').enabled()) or (PY_IMPL != 'cpython') or (skip_env != '')

py = import('python').find_installation(pure: pure_py)

py.install_sources(
    [
        'yarl/__init__.py',
        'yarl/py.typed',
        'yarl/_parse.py',
        'yarl/_path.py',
        'yarl/_query.py',
        'yarl/_quoters.py',
        'yarl/_quoting.py',
        'yarl/_quoting_py.py',
        'yarl/_url.py',
        'yarl/_quoting_c.pyx',
    ],
    subdir: 'yarl',
)

if not pure_py
    cython = find_program('cython')

    cython_args = ['-3']

    if get_option('cython-trace').enabled()
        cython_args += ['-X', 'linetrace=True']
        add_global_arguments('-DCYTHON_TRACE=1', language: 'c')
        add_global_arguments('-DCYTHON_USE_SYS_MONITORING=0', language: 'c')
    endif

    cython_gen = generator(
        cython,
        output: ['@BASENAME@.c'],
        arguments: ['@INPUT@', '--output-file', '@OUTPUT0@'] + cython_args,
    )

    quoting_c = cython_gen.process(
        'yarl/_quoting_c.pyx',
        preserve_path_from: meson.current_source_dir(),
    )

    out = py.extension_module(
        '_quoting_c',
        quoting_c,
        subdir: 'yarl',
        install: true,
        dependencies: py.dependency(),
    )

    copy_c = custom_target(
        'copy generated c file back to source tree',
        input: quoting_c,
        output: 'copy_c',
        build_by_default: false,
        command: [
            'cp',
            '@INPUT@',
            join_paths(meson.project_source_root(), 'yarl/'),
        ],
    )

    # support for in-tree build
    # # will target will copy binary extension back to source directory
    custom_target(
        'copy extension back to source tree',
        input: out,
        output: 'copy',
        depends: [out, copy_c],
        command: [
            'cp',
            out.full_path(),
            join_paths(meson.project_source_root(), 'yarl/'),
        ],
        build_by_default: false,
    )
endif
