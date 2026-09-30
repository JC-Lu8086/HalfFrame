# SPDX-License-Identifier: MIT
# Copyright (C) 2026 J.C. Lu
"""Assemble a Windows x64 portable package without installing Python on Windows.

Run on any platform with Python 3.10+ and pre-downloaded Windows wheels:
  python build_windows_portable.py --python-zip python-3.12.10-embed-amd64.zip \
      --wheels wheels --output HalfFrame-Windows-x64 --zip HalfFrame-Windows-x64.zip

Use the official Python embeddable distribution and binary wheels for its Python
version, the win_amd64 architecture, and the dependencies in requirements.txt.
No network access or system installation is performed by this script.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import struct
import tempfile
from zipfile import ZIP_DEFLATED, ZipFile


REQUIRED_PACKAGES = {
    'numpy', 'pillow', 'tifffile', 'imagecodecs', 'piexif',
    'pyside6_essentials', 'shiboken6',
}
IGNORED = shutil.ignore_patterns(
    '__pycache__', '*.pyc', '*.pyo', '.DS_Store', '.pytest_cache',
    '.git', '.venv', 'venv', 'build', 'dist', '*.egg-info',
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def archive_path(name: str) -> PurePosixPath:
    """Reject archive members that could escape the chosen output directory."""
    path = PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts or '\\' in name or ':' in name:
        raise ValueError(f'Unsafe archive member: {name!r}')
    return path


def unpack(archive_file: Path, target: Path, *, wheel: bool = False) -> None:
    with ZipFile(archive_file) as archive:
        for item in archive.infolist():
            relative = archive_path(item.filename)
            if not relative.parts:
                continue
            if wheel and relative.parts[0].endswith('.data'):
                # Wheel .data/purelib and .data/platlib have the same destination
                # in this private runtime. No downloaded scripts are executed.
                if len(relative.parts) < 3 or relative.parts[1] not in {'purelib', 'platlib'}:
                    raise ValueError(f'Unsupported wheel data layout: {item.filename}')
                relative = PurePosixPath(*relative.parts[2:])
            destination = target.joinpath(*relative.parts)
            if item.is_dir():
                destination.mkdir(parents=True, exist_ok=True)
                continue
            if (item.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError(f'Symlink in input archive: {item.filename}')
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                # Namespace package directories may be shared, files must agree.
                content = archive.read(item)
                if destination.read_bytes() != content:
                    raise ValueError(f'Conflicting archive file: {relative}')
            else:
                with archive.open(item) as source, destination.open('wb') as output:
                    shutil.copyfileobj(source, output)


def pe_machine(path: Path) -> int:
    with path.open('rb') as stream:
        if stream.read(2) != b'MZ':
            raise ValueError(f'Not a Windows executable: {path.name}')
        stream.seek(0x3C)
        offset = struct.unpack('<I', stream.read(4))[0]
        stream.seek(offset)
        if stream.read(4) != b'PE\0\0':
            raise ValueError(f'Invalid PE header: {path.name}')
        return struct.unpack('<H', stream.read(2))[0]


def copy_source(source: Path, target: Path) -> None:
    # Keep complete editable application source and all third-party notices.
    for path in source.iterdir():
        if path.name in IGNORED(str(source), [path.name]):
            continue
        if path.is_dir():
            if path.name not in {'halfframe', 'tests', 'licenses', 'bin'}:
                continue
            shutil.copytree(path, target / path.name, ignore=IGNORED)
        elif path.name == 'LICENSE' or path.suffix.lower() in {'.py', '.md', '.txt', '.bat', '.command'}:
            shutil.copy2(path, target / path.name)


def pe_imports(path: Path) -> set[str]:
    """Read direct and delayed DLL imports without executing downloaded code."""
    data = path.read_bytes()
    pe = struct.unpack_from('<I', data, 0x3C)[0]
    sections = struct.unpack_from('<H', data, pe + 6)[0]
    optional_size = struct.unpack_from('<H', data, pe + 20)[0]
    optional = pe + 24
    if struct.unpack_from('<H', data, optional)[0] != 0x20B:
        raise ValueError(f'Expected PE32+ binary: {path}')
    section_start = optional + optional_size
    def offset(rva):
        for index in range(sections):
            start = section_start + index * 40
            virtual_size, virtual_address, raw_size, raw_offset = struct.unpack_from('<IIII', data, start + 8)
            if virtual_address <= rva < virtual_address + max(virtual_size, raw_size):
                return raw_offset + rva - virtual_address
        raise ValueError(f'Invalid import RVA in {path.name}')
    imports = set()
    for directory, entry_size, name_index in ((1, 20, 3), (13, 32, 1)):
        rva, size = struct.unpack_from('<II', data, optional + 112 + directory * 8)
        if not rva:
            continue
        cursor = offset(rva)
        end = min(len(data), cursor + size)
        while cursor + entry_size <= end:
            entry = struct.unpack_from('<' + 'I' * (entry_size // 4), data, cursor)
            if not any(entry):
                break
            name_offset = offset(entry[name_index])
            imports.add(data[name_offset:data.index(0, name_offset)].decode('ascii').lower())
            cursor += entry_size
    return imports


def select_qt_runtime(site_packages: Path) -> list[str]:
    """Ship the Widgets runtime and its dependencies, excluding unused tools/QML."""
    qt = site_packages / 'PySide6'
    plugins = {'platforms/qwindows.dll', 'platforms/qoffscreen.dll',
               'styles/qmodernwindowsstyle.dll', 'imageformats/qjpeg.dll',
               'imageformats/qgif.dll', 'imageformats/qico.dll',
               'imageformats/qsvg.dll', 'iconengines/qsvgicon.dll'}
    roots = [qt / name for name in ('QtCore.pyd', 'QtGui.pyd', 'QtWidgets.pyd', 'pyside6.abi3.dll')]
    roots += [qt / 'plugins' / name for name in plugins]
    libraries = {p.name.lower(): p for p in qt.glob('*.dll')}
    keep = {p.name.lower() for p in roots}
    pending = list(roots)
    while pending:
        item = pending.pop()
        for name in pe_imports(item):
            if name in libraries and name not in keep:
                keep.add(name)
                pending.append(libraries[name])
    for item in qt.iterdir():
        if (item.name.startswith('Qt6') and item.suffix == '.dll' and item.name.lower() not in keep
                or item.suffix == '.pyd' and item.name.lower() not in keep
                or item.suffix == '.exe' or item.name.startswith('pyside6qml.')):
            item.unlink()
    for item in (qt / 'plugins').rglob('*.dll'):
        if item.relative_to(qt / 'plugins').as_posix() not in plugins:
            item.unlink()
    shutil.rmtree(qt / 'qml', ignore_errors=True)
    return sorted(p.name for p in qt.glob('Qt6*.dll'))


def build(python_zip: Path, wheels: Path, output: Path, zip_output: Path | None) -> None:
    source = Path(__file__).resolve().parent
    output = output.resolve()
    if output.exists():
        raise FileExistsError(f'Output already exists: {output}')
    if zip_output is not None and zip_output.exists():
        raise FileExistsError(f'ZIP output already exists: {zip_output}')
    wheel_paths = sorted(wheels.glob('*.whl'))
    packages: dict[str, Path] = {}
    for path in wheel_paths:
        parts = path.name[:-4].split('-')
        if len(parts) < 5 or parts[-1] not in {'win_amd64', 'any'}:
            raise ValueError(f'Expected a Windows x64 or pure-Python wheel: {path.name}')
        package = parts[0].lower().replace('-', '_')
        if package in packages:
            raise ValueError(f'Duplicate package wheel: {package}')
        packages[package] = path
    if missing := REQUIRED_PACKAGES - packages.keys():
        raise ValueError(f'Missing dependency wheels: {", ".join(sorted(missing))}')
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.halfframe-windows-', dir=output.parent))
    try:
        runtime = staging / 'runtime'
        runtime.mkdir()
        unpack(python_zip, runtime)
        path_files = list(runtime.glob('python*._pth'))
        if len(path_files) != 1:
            raise ValueError('Expected exactly one Python embeddable ._pth file')
        python_name = path_files[0].stem
        if not (runtime / f'{python_name}.zip').is_file():
            raise ValueError('The embedded Python standard library archive is missing')
        python_version = python_name.removeprefix('python')
        for path in wheel_paths:
            fields = path.stem.split('-')
            py_tag, abi_tag = fields[-3:-1]
            if abi_tag not in {'none', 'abi3'} and abi_tag != f'cp{python_version}':
                raise ValueError(f'Wheel ABI does not match embedded Python: {path.name}')
            if abi_tag == 'abi3' and py_tag.startswith('cp'):
                required = (int(py_tag[2]), int(py_tag[3:]))
                available = (int(python_version[0]), int(python_version[1:]))
                if required > available:
                    raise ValueError(f'Wheel needs a newer Python: {path.name}')
        site_packages = runtime / 'Lib' / 'site-packages'
        site_packages.mkdir(parents=True)
        for path in wheel_paths:
            unpack(path, site_packages, wheel=True)
        # These optional codecs require separately licensed external SDKs and
        # are unnecessary for standard JPG/TIFF. Never ship their unusable stubs.
        for name in ('_heif.pyd', '_jetraw.pyd', '_jpegxs.pyd'):
            (site_packages / 'imagecodecs' / name).unlink(missing_ok=True)
        qt_libraries = select_qt_runtime(site_packages)
        # Entries are relative to the embedded interpreter, so a moved/unzipped
        # package works equally in spaces, Unicode paths, and a different drive.
        path_files[0].write_text(
            f'{python_name}.zip\n.\nLib/site-packages\n../app\nimport site\n',
            encoding='utf-8',
        )
        app = staging / 'app'
        app.mkdir()
        copy_source(source, app)
        shutil.copy2(app / 'WINDOWS-NOTICE.md', staging / 'WINDOWS-NOTICE.md')
        for name in ('jpegtran.exe', 'jpeg62.dll'):
            if not (app / 'bin' / name).is_file():
                raise ValueError(f'Missing bundled JPEG tool: bin/{name}')
        # jpegtran is a child process and needs its runtime beside its executable.
        for dll in runtime.glob('vcruntime*.dll'):
            shutil.copy2(dll, app / 'bin' / dll.name)
        for binary in staging.rglob('*'):
            if binary.suffix.lower() in {'.dll', '.exe', '.pyd'}:
                if pe_machine(binary) != 0x8664:
                    raise ValueError(f'Non-x64 binary in package: {binary.relative_to(staging)}')
        (staging / 'HalfFrame.cmd').write_bytes(
            b'@echo off\r\nsetlocal\r\ncd /d "%~dp0"\r\n'
            b'start "" "%~dp0runtime\\pythonw.exe" "%~dp0app\\app.py" %*\r\n'
        )
        (staging / 'HalfFrame-debug.cmd').write_bytes(
            b'@echo off\r\nsetlocal\r\ncd /d "%~dp0"\r\n'
            b'"%~dp0runtime\\python.exe" "%~dp0app\\app.py" %*\r\n'
            b'echo.\r\npause\r\n'
        )
        (staging / 'README.txt').write_text(
            'HalfFrame 0.2.1 — J.C. Lu\n\n'
            'Windows 10/11 x64 便携版\n'
            '请先解压整个文件夹，再双击 HalfFrame.cmd。无需安装 Python。\n'
            '请勿单独移动启动文件；app 和 runtime 必须一起保留。\n'
            '如无法启动，运行 HalfFrame-debug.cmd 查看错误。\n'
            '完整中英双语说明、版本记录与 MIT 许可证见 app 文件夹。\n'
            '第三方组件保留各自许可证，详见 app/THIRD_PARTY_NOTICES.md。\n\n'
            'Windows 10/11 x64 portable edition\n'
            'Extract the complete folder, then double-click HalfFrame.cmd. '
            'Python installation is not required.\n'
            'Keep the launchers, app, and runtime together when moving this folder.\n'
            'If startup fails, run HalfFrame-debug.cmd to see the error message.\n'
            'Bilingual instructions, changelog, and the MIT application license are in app.\n'
            'Third-party components retain their own licenses; see app/THIRD_PARTY_NOTICES.md.\n\n'
            'The author does not have a Windows computer. The Windows version has not been tested on Windows.\n'
            'This package was assembled and structurally checked on macOS. '
            'A Windows runtime test is still required.\n'
            '作者没有 Windows 电脑，因此 Windows 版本尚未经过实际运行测试。\n'
            '此包已在 macOS 组装并完成结构检查，尚需 Windows 实机验证。\n',
            encoding='utf-8',
        )
        manifest = {
            'application': 'HalfFrame', 'version': '0.2.1', 'author': 'J.C. Lu',
            'platform': 'Windows x64', 'application_license': 'MIT',
            'python_archive': {'file': python_zip.name, 'sha256': sha256(python_zip)},
            'wheels': [{'file': path.name, 'sha256': sha256(path)} for path in wheel_paths],
            'jpeg_tools': {
                name: sha256(app / 'bin' / name) for name in ('jpegtran.exe', 'jpeg62.dll')
            },
            'checks': ['relative interpreter paths', 'all native binaries are AMD64',
                       'all seven runtime dependency wheels included', 'original wheel license metadata retained'],
            'windows_execution_tested': False,
            'qt_libraries': qt_libraries,
            'qt_selection': 'Unmodified Widgets libraries and required DLLs; unused tools and QML omitted.',
        }
        (staging / 'BUILD-MANIFEST.json').write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + '\n', encoding='utf-8',
        )
        staging.rename(output)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    if zip_output is not None:
        zip_output.parent.mkdir(parents=True, exist_ok=True)
        with ZipFile(zip_output, 'x', compression=ZIP_DEFLATED, compresslevel=6) as archive:
            for path in sorted(output.rglob('*')):
                if path.is_file():
                    archive.write(path, path.relative_to(output.parent).as_posix())
    print(f'Created {output.name}' + (f' and {zip_output.name}' if zip_output else ''))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--python-zip', required=True, type=Path, help='Official Windows x64 embeddable Python ZIP')
    parser.add_argument('--wheels', required=True, type=Path, help='Directory containing matching dependency .whl files')
    parser.add_argument('--output', required=True, type=Path, help='New portable application directory')
    parser.add_argument('--zip', dest='zip_output', type=Path, help='Optional new distribution ZIP')
    args = parser.parse_args()
    build(args.python_zip, args.wheels, args.output, args.zip_output)


if __name__ == '__main__':
    main()
