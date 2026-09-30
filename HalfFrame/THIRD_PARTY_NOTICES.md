# 第三方声明 / Third-party notices

HalfFrame / 半格 — J.C. Lu  
Copyright (C) 2026 J.C. Lu — project-specific contributions / 本项目自行编写部分。  
Project license / 项目许可证：**MIT**。完整英文正文见 [LICENSE](LICENSE)。

本项目的署名及 MIT 声明不取代第三方的作者署名、版权或许可证，也不适用于用户导入或导出的照片。第三方组件并非全部采用 MIT。以下是对已检查组件的许可记录，不是对所有源码原创性、专利或最终安装包合规性的保证。

The project attribution and MIT grant do not replace third-party copyrights or licenses and do not license the photographs imported or exported by users. Third-party components are not all MIT. This is a record of inspected component terms, not a guarantee of universal source originality, patent clearance, or compliance of every future binary package.

## 已核实组件 / Inspected components

版本来自本次构建环境；新构建若更新依赖，应同步更新此表和附带条款。每个组件的原文与版权声明优先于下列摘要。

Versions below were inspected in the build environment. Update this table and the accompanying terms whenever dependencies change. Original license texts and copyright notices control over these summaries.

| 组件 / Component | 已检查版本 / Inspected version | 许可及署名 / License and attribution | 随附记录 / Included record |
|---|---|---|---|
| CPython | macOS: 3.12.14; Windows embedded: 3.12.10 | PSF License Version 2 and historical Python terms; Python Software Foundation and prior contributors | `licenses/Python-LICENSE.txt` |
| PySide6-Essentials | 6.11.2 | Wheel metadata: `LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only`; The Qt Company and contributors. The LGPLv3 option is used for the unmodified dynamically linked bindings. | `licenses/Qt/`; `licenses/package-metadata/pyside6_essentials-6.11.2.txt` |
| shiboken6 | 6.11.2 | Same license alternatives as PySide6; LGPLv3 option for the unmodified runtime; The Qt Company and contributors | `licenses/Qt/`; `licenses/package-metadata/shiboken6-6.11.2.txt` |
| Qt Core / Gui / Widgets and collected Qt plugins | 6.11.2 | Qt open-source LGPLv3/GPL alternatives depend on the module; the application uses the LGPLv3 option for eligible shared libraries. Embedded third-party code retains separate terms. | `licenses/Qt/`; [Qt licensing](https://doc.qt.io/qt-6/licensing.html), [Qt for Python third-party licenses](https://doc.qt.io/qtforpython-6/licenses.html) |
| NumPy | 2.5.3 | BSD-3-Clause; NumPy Developers. The wheel also carries OpenBLAS, LAPACK, GCC runtime and other notices; these must be retained. | `licenses/numpy/` |
| Pillow / PIL | 12.3.0 | MIT-CMU; Secret Labs AB, Fredrik Lundh, Jeffrey “Alex” Clark and contributors. The included license also covers bundled codecs under their own terms. | `licenses/pillow/` |
| tifffile | 2026.9.20 | BSD-3-Clause; Christoph Gohlke | `licenses/tifffile/` |
| imagecodecs | 2026.8.16 | BSD-3-Clause for the wrapper; Christoph Gohlke. Individual codecs have distinct licenses, including BSD, MIT, Apache-2.0, zlib and other notices. | `licenses/imagecodecs/` |
| piexif | 1.1.3 | MIT; hMatoba | `licenses/piexif/` |
| libjpeg-turbo / jpegtran | macOS: 3.1.2; Windows supplied component: 3.2.0 | IJG license and BSD-3-Clause, with zlib-licensed SIMD sources; Independent JPEG Group, D. R. Commander, Viktor Szathmáry and other contributors | `licenses/libjpeg-turbo-LICENSE.md`; `licenses/libjpeg-turbo-windows/` |
| PyInstaller bootloader and runtime hooks | 6.22.3 | GPL-2.0-or-later with the bootloader exception; runtime hooks and specified helper modules use Apache-2.0. PyInstaller Development Team and prior contributors. | `licenses/PyInstaller/COPYING.txt` |

### 必须保留的致谢 / Retained acknowledgments

This software is based in part on the work of the Independent JPEG Group.

本软件部分基于 Independent JPEG Group 的成果。

The imagecodecs distribution includes the SZ3 license and acknowledgment:

“This product includes software produced by UChicago Argonne, LLC under Contract No. DE-AC02-06CH11357 with the Department of Energy.”

imagecodecs 内的 SZ3、HDF5、zfp 等组件的附加版权和政府资助声明完整保留于 `licenses/imagecodecs/imagecodecs/licenses/`。上述致谢不表示这些机构为本产品背书。

Additional SZ3, HDF5, zfp and other copyright/government-funding notices are retained in full under `licenses/imagecodecs/imagecodecs/licenses/`. These acknowledgments do not imply endorsement.

## 发布及源码 / Distribution and source

1. **项目代码 / Application source.** 本项目自行编写部分采用 MIT；复制或分发本软件的重要部分时，须保留 J.C. Lu 的版权及 MIT 许可声明。MIT 允许修改、再分发、再许可及商业使用，本身不强制公开衍生应用的源码。本包附带源码、测试及构建说明，方便修改与重建；软件不提供保证，详见许可正文。Project-specific code is MIT licensed. Copies or substantial portions must retain J.C. Lu's copyright and the MIT notice. MIT permits modification, redistribution, sublicensing and commercial use and does not itself require publishing derivative application source. Source, tests and build instructions are supplied to enable modification and rebuilding. The software is provided without warranty as specified in the license.

2. **Qt / PySide / Shiboken.** 使用 LGPLv3 动态库选项，HalfFrame 自编代码继续采用 MIT。发行包直接附带匹配 6.11.2 的 QtBase、QtSvg、pyside-setup 完整上游源码归档，包含构建脚本及上游许可；官方校验值见 `third_party_sources/manifest.json`。允许修改/替换兼容的 LGPL 库、为调试修改进行逆向工程，并运行重新链接的应用。具体文件位置、重建与 Mac 本地重新签名说明见 [RELINKING.md](RELINKING.md)。应用侧栏显示 Qt 署名和 LGPLv3 使用提示，许可窗口可离线查看 LGPLv3、GPLv3、第三方声明和源码说明。各原始许可条款优先。

   The LGPLv3 dynamic-library option is used; HalfFrame application code remains MIT. Matching QtBase, QtSvg and pyside-setup 6.11.2 source archives, including build scripts and upstream notices, are delivered in `third_party_sources/`, with official SHA-256 values recorded. Modification/replacement, reverse engineering to debug such modifications, and running relinked applications are permitted. See [RELINKING.md](RELINKING.md) for locations, rebuild entry points and ad-hoc re-signing. The app visibly credits Qt and exposes license texts/source-delivery information offline.

3. **保持随附声明 / Preserve notices.** 将 `LICENSE`、本文件和 `licenses/` 随源码与二进制包一起交付；保留各组件的上游版权、许可正文及 NOTICE。修改第三方源文件时记录修改及日期，不将 J.C. Lu 写成第三方代码的原作者。Ship `LICENSE`, this file and `licenses/` with source and binary distributions; preserve upstream notices, license texts and NOTICE files. Record changes to third-party sources and their dates; do not attribute their original authorship to J.C. Lu.

4. **构建记录 / Build record.** 保存实际所用轮子、库、编译器/打包器版本、来源与必要补丁。具体二进制包所包含的组件清单应以该包为准，不能仅以 Python 的 requirements 文件推断。Record actual wheels, libraries, compiler/packager versions, origins and required patches. A binary package’s inventory must reflect that package, not merely its Python requirements file.

上游源码入口 / Upstream source locations: [CPython](https://github.com/python/cpython), [Qt](https://code.qt.io/cgit/qt/), [Qt for Python / Shiboken](https://code.qt.io/cgit/pyside/pyside-setup.git/), [Qt for Python releases](https://download.qt.io/official_releases/QtForPython/), [NumPy](https://github.com/numpy/numpy), [Pillow](https://github.com/python-pillow/Pillow), [tifffile](https://github.com/cgohlke/tifffile), [imagecodecs](https://github.com/cgohlke/imagecodecs), [piexif](https://github.com/hMatoba/Piexif), [libjpeg-turbo](https://github.com/libjpeg-turbo/libjpeg-turbo), [PyInstaller](https://github.com/pyinstaller/pyinstaller). These links identify upstream projects. The applicable Qt/PySide/Shiboken source archives are delivered locally in third_party_sources; no future written source offer is used. / 上述链接标识上游项目；Qt/PySide/Shiboken 的对应源码已实际随包交付，不采用日后兑现的书面承诺。

## 兼容性核查范围 / Compatibility audit scope

MIT 应用可以使用符合 LGPLv3 条件的动态链接库；将本项目改为 MIT 不会给 Qt 或其他依赖重新授权。这里选用 Qt/PySide/Shiboken 的 LGPLv3 路径；不得把仅有 GPL 许可的其他 Qt 模块未经复核加入并宣称整个组合仍只有 MIT 条件。当前 Windows NumPy 轮子标明 OpenBLAS/LAPACK 及 GCC runtime（`GPL-3.0-or-later WITH GCC-exception-3.1`），已保留完整原文。许可文件中的历史附录不自动说明该组件实际存在于本包。

An MIT application can use dynamically linked LGPLv3 libraries while meeting their conditions. Changing this project's license does not relicense Qt or other dependencies. The LGPLv3 option is selected for Qt/PySide/Shiboken; adding GPL-only Qt modules requires a separate review and cannot be described as an MIT-only combination. The Windows NumPy wheel identifies OpenBLAS/LAPACK and GCC runtime under `GPL-3.0-or-later WITH GCC-exception-3.1`; full notices and exceptions are retained. Historical appendices alone do not establish that a component is present. See [Qt licensing](https://doc.qt.io/qt-6/licensing.html).

imagecodecs 的源码项目支持的可选库多于当前平台实际安装的库。当前 macOS 安装中没有 Jetraw、HEIF 或 JPEG XS 扩展；Windows 包也排除这些需另行提供外部 SDK 的可选扩展；其许可证目录中的同名空占位文件不是授权证明。以后若增加这些或其他可选二进制，需单独检查其实际许可与分发条件。Qt 插件、Pillow 编码库、系统运行库及不同平台轮子的完整构成也应在最终发布包上核对。本记录不替代该检查。

The imagecodecs source project supports more optional libraries than are installed on this platform. No Jetraw, HEIF or JPEG XS extension was present in the inspected macOS installation; their optional Windows stubs are excluded from the portable package because the required external SDKs are not bundled; empty matching license placeholders are not evidence of permission. Newly bundled optional binaries require their own license/distribution review. The final package must also be checked for Qt plugins, Pillow codecs, system runtimes and platform-specific wheel contents. This record does not replace that check.

**Windows 运行库 / Windows runtimes.** 原始 Windows Python 许可、微软官方参考条款以及逐文件来源/哈希已保留于 `licenses/Microsoft/` 和 `licenses/Python-Windows-LICENSE.txt`。DLL 均追溯到原始 Python 嵌入包或依赖 wheels，内容未修改；未复制个人系统目录内的任意 DLL。微软组件不采用 MIT。发行者已确认持有并接受 Visual Studio Community 许可，本次以该确认作为其资格记录。原始中英运行库终端条款已附，Windows 首次启动要求主动确认，记录仅保存本机。第三方分发者仍需自行具备适用权利，不能把本记录当作新的授权。详见 [RELEASE-LICENSING.md](RELEASE-LICENSING.md)。

Original Windows Python conditions, official Microsoft reference terms, and per-file provenance/hashes are retained. DLLs are unchanged upstream archive/wheel files, not arbitrary copies from a personal system. They are not MIT licensed. The publisher confirmed holding and accepting Visual Studio Community licensing. Original English/Chinese runtime terms are included and Windows first launch requests affirmative acknowledgement stored locally. This records publisher confirmation, not independent entitlement certification; downstream distributors need applicable authority.

本记录检查日期 / Audit date: 2026-09-30.

## 本次二进制选择 / Binary selection

仅随应用保留 Qt Core、Gui、Widgets、Svg，以及 macOS 所需的 DBus 和相关平台/图像插件；不包含未使用的 Qt PDF、Virtual Keyboard、QML、设计器或开发工具。各动态库未经源码修改。

The application packages retain Qt Core, Gui, Widgets, Svg, macOS DBus where required, and selected platform/image plugins. Unused Qt PDF, Virtual Keyboard, QML, designers and development tools are omitted. The shared libraries are unmodified.
