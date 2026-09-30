# 替换运行库与重建 / Library replacement and rebuilding

HalfFrame 0.2.2 · J.C. Lu

HalfFrame 自编代码采用 MIT；Qt、PySide、Shiboken 采用各自 LGPLv3 许可。允许修改、替换兼容的 LGPL 库，为调试这些修改进行逆向工程，并运行修改后的应用。不存在应用层库哈希锁定、联网授权或必须持有作者签名密钥的要求。微软专有组件的独立条款不限制这些 LGPL 权利。

## 直接替换 / Direct replacement

先复制应用作为备份并退出运行中的应用。替换库必须匹配体系结构、Python ABI、Qt 6.11 的接口，以及库文件名和相互依赖；保留符号链接结构。随附源码为 6.11.2。

**macOS Apple Silicon:** 在 Finder 中右键应用 → 显示包内容。Qt 库位于 `Contents/Frameworks/PySide6/Qt/lib/`，插件位于 `Contents/Frameworks/PySide6/Qt/plugins/`；PySide 绑定位于 `Contents/Frameworks/PySide6/`，Shiboken 位于 `Contents/Frameworks/shiboken6/`。替换所需的 arm64 库与兼容插件，维持 `@rpath` / `@loader_path` 引用。打包器创建的 Resources 符号链接应继续指向同一文件。替换会使原签名失效，可在终端对自己的副本重新做本地签名：

```sh
codesign --force --deep --sign - "/path/to/HalfFrame.app"
codesign --verify --deep --strict "/path/to/HalfFrame.app"
```

路径由使用者替换；不需要 J.C. Lu 的密钥、Apple 开发者付费证书或联网。重签名不等于 Apple 公证，也不会替代系统可能要求的打开确认。

**Windows x64:** Qt/PySide 位于 `runtime/Lib/site-packages/PySide6/`，Shiboken 位于相邻的 `shiboken6/`。替换相应 `.dll`、`.pyd` 和插件，保持 x64 / CPython 3.12 兼容；可通过 `HalfFrame-debug.cmd` 查看加载错误。不要把对 LGPL 库的替换许可理解为微软 DLL 的修改许可。Windows 实机未测试。

## 从源码重建 / Rebuild from source

项目源码包包含 app.py、halfframe、测试和打包脚本；Mac 应用内也有 `Contents/Resources/source/`。先解压 third_party_sources 内的三个源码包，保留其构建文件与 LICENSES。

QtBase 的通用构建入口（使用当前平台的 C++ 工具链、CMake 和 Ninja）：

```sh
cmake -S qtbase-everywhere-src-6.11.2 -B build-qtbase -G Ninja \
  -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=ON \
  -DQT_BUILD_TESTS=OFF -DQT_BUILD_EXAMPLES=OFF -DCMAKE_INSTALL_PREFIX=/your/qt-prefix
cmake --build build-qtbase
cmake --install build-qtbase
mkdir build-qtsvg
cd build-qtsvg
/your/qt-prefix/bin/qt-configure-module /absolute/path/to/qtsvg-everywhere-src-6.11.2
cmake --build .
cmake --install .
```

QtSvg 应在单独的空构建目录中调用上面的 qt-configure-module（将源码路径改为实际路径），再执行 `cmake --build .` 和 `cmake --install .`。Windows 使用相应 `.bat` 工具、绝对 Windows 路径和 x64 开发者命令提示符；macOS 使用 Xcode Command Line Tools。具体依赖和配置选项见各源码包内 README 和构建文件。这里给出修改/重建入口，不承诺生成与上游逐字节相同的库。

PySide/Shiboken 的源码在 pyside-setup 中。根据包内构建文档准备匹配的 libclang/LLVM 和 Python 3.12 开发环境，在该目录执行：

```sh
python setup.py bdist_wheel --qtpaths=/your/qt-prefix/bin/qtpaths --ignore-git
```

将生成的、匹配本机架构的 PySide6_Essentials 和 Shiboken6 wheels 安装到新的 Python 环境，再运行 HalfFrame 源码：

```sh
python -m venv .venv
# Activate this environment using the command for your operating system.
python -m pip install -r requirements-release.txt
# Install your replacement wheels here, after dependencies.
python -m pip install --force-reinstall --no-deps /path/to/your/replacement.whl
python app.py
```

依赖的联网下载只用于开发环境搭建，照片处理不联网。Mac 完整应用可通过 `python build.py` 重建（另需 PyInstaller 6.22.3 和 jpegtran）。Windows 可用 `build_windows_portable.py --help` 查看离线组装参数；自行提供官方 Python 嵌入包、匹配 wheels，以及通过 `--jpeg-tools` 指定的 jpegtran 工具目录。使用自己的修改库替换输入 wheels 后组装。

## English

You may modify and replace compatible LGPL libraries, reverse engineer to debug those modifications, and run the modified application. HalfFrame applies no library hash lock, remote authorization requirement, or developer-key requirement. Separate Microsoft terms do not restrict these LGPL rights.

Back up the app and close it before replacement. On macOS, replace arm64 Qt frameworks/plugins under Contents/Frameworks/PySide6/Qt, the PySide bindings under Contents/Frameworks/PySide6, and Shiboken under Contents/Frameworks/shiboken6. Preserve symlinks, ABI compatibility and relative loader references. Re-sign your own copy with the ad-hoc codesign commands above; no author's key or paid Apple certificate is required. On Windows replace compatible x64 DLL/PYD files in runtime/Lib/site-packages/PySide6 and shiboken6, then use the debug launcher for diagnostics. Windows execution remains untested.

The three included source archives contain the upstream build machinery. Build shared QtBase and QtSvg, then build pyside-setup with matching Qt, Python 3.12 and libclang/LLVM. Install replacement wheels into a fresh application environment after dependencies; launch app.py or rebuild the app with the supplied scripts. Commands above are rebuild entry points, not a claim of bit-for-bit reproducibility of upstream wheels. Preserve all applicable notices when redistributing modifications.
