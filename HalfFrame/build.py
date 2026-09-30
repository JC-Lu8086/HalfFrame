# SPDX-License-Identifier: MIT
# Copyright (C) 2026 J.C. Lu
"""Build a standalone application on its target OS; paths are relocatable."""
from pathlib import Path
import argparse
import os
import plistlib
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def select_mac_qt_runtime(bundle):
    """Keep Widgets and its linked frameworks; omit unused tools and plugins."""
    qt = bundle / 'Contents' / 'Frameworks' / 'PySide6' / 'Qt'
    plugins = {'platforms/libqcocoa.dylib', 'platforms/libqoffscreen.dylib',
               'platforms/libqminimal.dylib', 'styles/libqmacstyle.dylib',
               'imageformats/libqjpeg.dylib', 'imageformats/libqgif.dylib',
               'imageformats/libqico.dylib', 'imageformats/libqsvg.dylib',
               'iconengines/libqsvgicon.dylib'}
    keep = {'QtCore', 'QtGui', 'QtWidgets'}
    roots = [qt / 'lib' / (name + '.framework') / 'Versions' / 'A' / name for name in keep]
    pending = roots + [qt / 'plugins' / name for name in plugins]
    while pending:
        item = pending.pop()
        linked = subprocess.check_output(['otool', '-L', str(item)], text=True)
        dependencies = re.findall(r'(Qt\w+)\.framework/', linked)
        dependencies += re.findall(r'@rpath/(Qt\w+)\s', linked)
        for name in dependencies:
            if name not in keep:
                keep.add(name)
                pending.append(qt / 'lib' / (name + '.framework') / 'Versions' / 'A' / name)
    for item in (qt / 'lib').glob('Qt*.framework'):
        if item.stem in keep:
            continue
        for location in ('Frameworks', 'Resources'):
            target = bundle / 'Contents' / location / 'PySide6' / 'Qt' / 'lib' / item.name
            if target.is_symlink():
                target.unlink()
            elif target.exists():
                shutil.rmtree(target)
            (bundle / 'Contents' / location / item.stem).unlink(missing_ok=True)
    for item in (qt / 'plugins').rglob('*.dylib'):
        if item.relative_to(qt / 'plugins').as_posix() not in plugins:
            item.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--distpath', type=Path, default=ROOT / 'dist')
    parser.add_argument('--workpath', type=Path, default=ROOT / 'build')
    options = parser.parse_args()
    dist = options.distpath.resolve()
    work = options.workpath.resolve()
    work.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(ROOT))
    from halfframe import __version__
    from halfframe.release_assets import verify_release_assets
    verify_release_assets(ROOT)
    from halfframe.image_io import jpegtran_path
    binary = jpegtran_path()
    separator = os.pathsep
    args = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean',
            '--windowed', '--name', 'HalfFrame', '--distpath', str(dist),
            '--workpath', str(work), '--specpath', str(work),
            '--collect-data', 'imagecodecs', '--add-binary', f'{binary}{separator}bin']
    for excluded in ('cv2', 'onnxruntime', 'torch', 'matplotlib', 'tkinter',
                     'IPython', 'pytest', 'pandas', 'PySide6.QtQml',
                     'PySide6.QtQuick', 'PySide6.QtNetwork', 'PySide6.QtOpenGL'):
        args += ['--exclude-module', excluded]
    for item in ('licenses', 'third_party_sources', 'README.md', 'CHANGELOG.md', 'LICENSE',
                 'THIRD_PARTY_NOTICES.md', 'RELINKING.md', 'RELEASE-LICENSING.md', 'WINDOWS-RUNTIME-TERMS.md'):
        destination = item if (ROOT / item).is_dir() else '.'
        args += ['--add-data', f'{ROOT / item}{separator}{destination}']
    if sys.platform == 'darwin':
        args += ['--osx-bundle-identifier', 'local.halfframe.desktop']
    if os.name == 'nt':
        for dll in Path(binary).parent.glob('*.dll'):
            args += ['--add-binary', f'{dll}{separator}bin']
    args.append(str(ROOT / 'app.py'))
    subprocess.run(args, check=True, cwd=ROOT)
    bundle = dist / ('HalfFrame.app' if sys.platform == 'darwin' else 'HalfFrame')
    resources = bundle / 'Contents' / 'Resources' if sys.platform == 'darwin' else bundle
    if sys.platform == 'darwin':
        select_mac_qt_runtime(bundle)
    source = resources / 'source'
    source.mkdir(parents=True, exist_ok=True)
    # Copy a bounded source inventory, never the build/output directory itself.
    for item in ROOT.iterdir():
        if item.is_file() and (item.suffix.lower() in ('.py', '.md', '.txt', '.command', '.bat') or item.name == 'LICENSE'):
            shutil.copy2(item, source / item.name)
    for directory in ('halfframe', 'tests', 'licenses', 'bin'):
        shutil.copytree(ROOT / directory, source / directory, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.DS_Store'))
    if sys.platform == 'darwin':
        plist_path = bundle / 'Contents' / 'Info.plist'
        with plist_path.open('rb') as handle:
            info = plistlib.load(handle)
        info.update(CFBundleShortVersionString=__version__, CFBundleVersion=__version__,
                    NSHumanReadableCopyright='Copyright © 2026 J.C. Lu. MIT License.',
                    NSHighResolutionCapable=True, LSMinimumSystemVersion='14.0')
        with plist_path.open('wb') as handle:
            plistlib.dump(info, handle)
        subprocess.run(['codesign', '--force', '--deep', '--sign', '-', str(bundle)], check=True)
    print('Built:', bundle)


if __name__ == '__main__':
    main()
