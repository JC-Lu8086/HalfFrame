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

2. **Qt / PySide / Shiboken.** 本次检查的 macOS PySide 二进制通过动态库链接 Qt 和 Shiboken，采用 LGPLv3 许可选项；应用自身采用 MIT。应允许使用者修改/替换兼容库、为调试此类修改进行逆向工程，并能运行重新链接的应用。分发方还须提供 LGPLv3 与其所引用的 GPLv3 正文、清楚的使用通知、适用的库对应源码及必要安装信息。库未修改也不自动免除源码义务；仅附带 HalfFrame 源码或通用上游网址不足以代表全部义务已履行。The inspected macOS PySide binary dynamically links Qt and Shiboken under their LGPLv3 option; application code is MIT. Users must be able to modify/replace compatible libraries, reverse engineer for debugging those modifications, and run the relinked application. Distributors must also provide LGPLv3 and its referenced GPLv3 text, prominent notices, applicable corresponding library source and necessary installation information. Unmodified libraries are not automatically exempt from source obligations; application source or a generic upstream URL alone is not proof of compliance. See the included license texts and [Qt’s LGPL obligations](https://www.qt.io/development/open-source-lgpl-obligations).

3. **保持随附声明 / Preserve notices.** 将 `LICENSE`、本文件和 `licenses/` 随源码与二进制包一起交付；保留各组件的上游版权、许可正文及 NOTICE。修改第三方源文件时记录修改及日期，不将 J.C. Lu 写成第三方代码的原作者。Ship `LICENSE`, this file and `licenses/` with source and binary distributions; preserve upstream notices, license texts and NOTICE files. Record changes to third-party sources and their dates; do not attribute their original authorship to J.C. Lu.

4. **构建记录 / Build record.** 保存实际所用轮子、库、编译器/打包器版本、来源与必要补丁。具体二进制包所包含的组件清单应以该包为准，不能仅以 Python 的 requirements 文件推断。Record actual wheels, libraries, compiler/packager versions, origins and required patches. A binary package’s inventory must reflect that package, not merely its Python requirements file.

上游源码入口 / Upstream source locations: [CPython](https://github.com/python/cpython), [Qt](https://code.qt.io/cgit/qt/), [Qt for Python / Shiboken](https://code.qt.io/cgit/pyside/pyside-setup.git/), [Qt for Python releases](https://download.qt.io/official_releases/QtForPython/), [NumPy](https://github.com/numpy/numpy), [Pillow](https://github.com/python-pillow/Pillow), [tifffile](https://github.com/cgohlke/tifffile), [imagecodecs](https://github.com/cgohlke/imagecodecs), [piexif](https://github.com/hMatoba/Piexif), [libjpeg-turbo](https://github.com/libjpeg-turbo/libjpeg-turbo), [PyInstaller](https://github.com/pyinstaller/pyinstaller). These locations identify upstream projects; they are not a written source offer from this project. / 以上是上游项目入口，不是本项目作出的书面源码提供承诺。

## 兼容性核查范围 / Compatibility audit scope

MIT 应用可以使用符合 LGPLv3 条件的动态链接库；将本项目改为 MIT 不会给 Qt 或其他依赖重新授权。这里选用 Qt/PySide/Shiboken 的 LGPLv3 路径；不得把仅有 GPL 许可的其他 Qt 模块未经复核加入并宣称整个组合仍只有 MIT 条件。NumPy 的随附许可还列有 GCC runtime 的 `GPL-3.0-or-later WITH GCC-exception-3.1` 和 libquadmath 的 `LGPL-2.1-or-later`，应保留其例外与完整条款。

An MIT application can use dynamically linked LGPLv3 libraries while meeting their conditions. Changing this project's license does not relicense Qt or other dependencies. The LGPLv3 option is selected for Qt/PySide/Shiboken; adding GPL-only Qt modules requires a separate review and cannot be described as an MIT-only combination. NumPy’s notices also list GCC runtime under `GPL-3.0-or-later WITH GCC-exception-3.1` and libquadmath under `LGPL-2.1-or-later`; retain these terms and exceptions. See [Qt licensing](https://doc.qt.io/qt-6/licensing.html).

imagecodecs 的源码项目支持的可选库多于当前平台实际安装的库。当前 macOS 安装中没有 Jetraw、HEIF 或 JPEG XS 扩展；Windows 包也排除这些需另行提供外部 SDK 的可选扩展；其许可证目录中的同名空占位文件不是授权证明。以后若增加这些或其他可选二进制，需单独检查其实际许可与分发条件。Qt 插件、Pillow 编码库、系统运行库及不同平台轮子的完整构成也应在最终发布包上核对。本记录不替代该检查。

The imagecodecs source project supports more optional libraries than are installed on this platform. No Jetraw, HEIF or JPEG XS extension was present in the inspected macOS installation; their optional Windows stubs are excluded from the portable package because the required external SDKs are not bundled; empty matching license placeholders are not evidence of permission. Newly bundled optional binaries require their own license/distribution review. The final package must also be checked for Qt plugins, Pillow codecs, system runtimes and platform-specific wheel contents. This record does not replace that check.

**Windows 运行库 / Windows runtimes.** 若最终 Windows 包包含 Microsoft Visual C++ Runtime DLL，它们适用 Microsoft 的再分发许可，不会因同包分发而变为 MIT。仅分发获准的组件，并保留适用条款；不要将开发机器上的任意系统 DLL 当作自由软件复制。Microsoft Visual C++ Runtime DLLs, if included, retain Microsoft’s redistribution terms and do not become MIT. Include only redistributable components with applicable terms; arbitrary system DLLs are not automatically freely redistributable. See [Microsoft redistribution guidance](https://learn.microsoft.com/en-us/cpp/windows/redistributing-visual-cpp-files?view=msvc-170).

本记录检查日期 / Audit date: 2026-09-29.

## 本次二进制选择 / Binary selection

仅随应用保留 Qt Core、Gui、Widgets、Svg，以及 macOS 所需的 DBus 和相关平台/图像插件；不包含未使用的 Qt PDF、Virtual Keyboard、QML、设计器或开发工具。各动态库未经源码修改。

The application packages retain Qt Core, Gui, Widgets, Svg, macOS DBus where required, and selected platform/image plugins. Unused Qt PDF, Virtual Keyboard, QML, designers and development tools are omitted. The shared libraries are unmodified.
