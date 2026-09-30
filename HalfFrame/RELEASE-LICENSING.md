# 发布材料与范围 / Release materials and scope

HalfFrame 0.2.2 · J.C. Lu · 2026-09-30

## 已完成 / Completed

- HalfFrame 自编代码保留 MIT 与 J.C. Lu 署名；第三方代码不重新授权。
- Mac 包和源码包均实际交付 QtBase、QtSvg、PySide/Shiboken 6.11.2 的完整上游源码归档；附官方 SHA-256 核验结果、来源、原始许可与构建文件。
- LGPLv3/GPLv3 正文、应用内 Qt 使用/版权提示、离线许可入口，以及用户替换兼容库和重建/重新签名的说明已附。
- Python、NumPy、Pillow、tifffile、imagecodecs、piexif、libjpeg-turbo、PyInstaller 的原许可与必要致谢保留；Windows wheels 的许可另外保留。
- 提供固定 Python 依赖版本；源代码无开发者绝对路径依赖。库源码未修改；Mac 打包时调整加载路径并本地签名。
- 公开源码和 Mac 应用不包含 Windows EXE/DLL。

## Windows 二进制 / Windows binary

作者没有 Windows 电脑，尚未进行 Windows 实机测试。发行者已确认持有并接受 Visual Studio Community 许可，本次以该确认作为发行资格记录；未独立认证具体账号或产品版本。

微软 DLL 的来源与 SHA-256 已逐文件记录。原始 Python 条件、微软参考分发条款和从官方安装包提取的中英运行库使用条款保留于 licenses/Microsoft。首次 Windows 启动展示运行库条款，用户主动勾选同意后继续；拒绝则退出；确认只保存在本机当前用户设置中。MIT 与 LGPL 组件不受微软专有组件条款约束。

本材料不会给其他人授予微软再分发权。后续发行者仍需确保自身适用的分发资格、范围和下游条款，并保留各组件许可。构建脚本只有在发行者显式传入 --redistribution-confirmed 后才将 Windows 包标为已确认分发依据；该参数本身不是授权。

## 如何上传 / What to upload

本次发布文件为 HalfFrame-Mac-AppleSilicon-0.2.2.zip、HalfFrame-Windows-x64-0.2.2.zip 与 HalfFrame-Source-0.2.2.zip。三者已各自包含所需 Qt 源码目录及许可文件；保持完整，不要只取可执行程序或删除 third_party_sources。源码仓库可使用源代码包解压后的内容，第三方源码归档继续按其原许可证发布。

这些材料记录本次具体构建及已落实的分发措施，不是法律认证；更换依赖、平台或发布渠道后，需要相应更新组件及许可材料。

## English

HalfFrame's project-specific code is MIT with J.C. Lu attribution; dependencies retain their terms. The Mac and source archives directly include complete upstream QtBase, QtSvg and PySide/Shiboken 6.11.2 source archives, official checksum verification, original notices and build scripts. LGPL/GPL texts, visible library attribution, an offline license viewer, and replacement/rebuild/re-signing instructions accompany the app. Other dependencies' notices are preserved. No Windows EXE/DLL is included in public source or the Mac package.

The publisher confirmed holding and accepting Visual Studio Community licensing; this is recorded without independent authentication of account or product version. Windows first launch requires affirmative agreement to original runtime terms, stored only locally. Declining exits. Microsoft-specific restrictions do not apply to MIT/LGPL components. Further distributors must hold applicable rights; the build flag --redistribution-confirmed records their assertion, not a license grant. Windows execution remains untested.

Publish the complete Mac, Windows and source archives named above; retain third_party_sources and licenses. These materials document the concrete distribution measures and do not constitute legal certification. Reassess the inventory and terms when dependencies, platforms or distribution channels change.
