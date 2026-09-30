# 第三方源码 / Third-party source delivery

HalfFrame 0.2.2 · J.C. Lu · 2026-09-30

这里直接附带未修改的上游源码压缩包，不是仅提供下载链接，也不是需要日后兑现的书面承诺。每个包的 SHA-256 已与 Qt 官方服务器公布的值比对。版本、来源及校验值见 manifest.json 和 SHA256SUMS.txt。

| 归档 / Archive | 对应组件 / Components |
|---|---|
| qtbase-everywhere-src-6.11.2.tar.xz | Qt Core、Gui、Widgets、DBus，相关平台/图像/样式插件，内部第三方源码和构建脚本 |
| qtsvg-everywhere-src-6.11.2.tar.xz | Qt Svg、SVG 图像及图标插件，构建脚本 |
| pyside-setup-everywhere-src-6.11.2.tar.xz | PySide6、Shiboken6，绑定源码、生成器与构建脚本 |

每个归档保留自身完整目录和上游许可；不将整个源码归档重新授权为 MIT。归档也会包含该上游项目的其他模块、示例或工具；这些内容不代表其二进制被装入 HalfFrame。HalfFrame 实际选用的库见 THIRD_PARTY_NOTICES.md。

本目录随 Mac 应用（Contents/Resources/third_party_sources）、Windows 构建目录（app/third_party_sources）和项目源码包提供。发布完整包即可一并交付；不要为缩小体积删掉它。若另外拆分源码下载，应在同一个下载页面清楚提供相应源码的同等获取方式。

构建和替换说明见 ../RELINKING.md。HalfFrame 未修改这些库的源代码；打包时仅选择使用的模块，Mac 打包器会调整库加载路径并执行本地签名。

## English

This directory delivers the unmodified upstream source archives themselves, including their build scripts and notices. It is not merely a set of upstream links or a future written source offer. Each archive was checked against the SHA-256 published by the official Qt server; manifest.json records the versioned URL and checksum.

QtBase covers the selected Core/Gui/Widgets/DBus libraries and their platform/image/style plugins; QtSvg covers SVG; pyside-setup covers both PySide and Shiboken, including the binding generator and build machinery. Preserve each archive's original license terms. Source archives also contain upstream modules, examples and tools that are not shipped as HalfFrame binaries.

The source directory accompanies the Mac app, Windows build, and application source archive. Keep it with each release. See ../RELINKING.md for replacement and build instructions. No library-source patches were made by HalfFrame; macOS packaging adjusts library load paths and applies ad-hoc signatures.
