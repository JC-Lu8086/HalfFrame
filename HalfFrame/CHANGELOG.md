# 版本记录 / Changelog

作者 / Author: **J.C. Lu**

## 0.2.2 — 2026-09-30

### 中文

- 随包实际交付 QtBase、QtSvg、PySide/Shiboken 6.11.2 完整源码、来源及官方 SHA-256 校验值。
- 新增离线许可窗口、Qt 署名、第三方源码说明和库替换/重建说明。
- 保留 Windows 专属许可证，逐一记录微软 DLL 的上游归档和哈希；发行者已确认 Visual Studio Community 许可，新增仅针对微软运行库的首次启动条款确认。
- 公开源码及 Mac 包不再夹带 Windows JPEG EXE/DLL；Windows 构建可从明确的输入目录读取工具。
- 保留 0.2.1 的裁切算法和画质处理行为。

### English

- Deliver complete QtBase, QtSvg and PySide/Shiboken 6.11.2 sources with provenance and official SHA-256 checksums.
- Add offline license viewing, visible Qt attribution and library replacement/rebuild instructions.
- Preserve Windows-specific terms and trace Microsoft DLLs to upstream inputs; publisher Visual Studio Community licensing confirmed and first-launch runtime-terms acknowledgement added.
- Remove Windows JPEG EXE/DLL files from public source and Mac packages; accept explicit JPEG-tool inputs for Windows builds.
- Retain 0.2.1 detection and image-quality behavior.

## 0.2.1 — 2026-09-30

### 中文

- 修复低置信度分界被直接判为识别失败的退化；可定位的低对比扫描仍给出分片，并提示复核。
- 改用多个噪声阈值下的 RGB 均匀度识别中心带，减少暗场背景与分隔带混淆。
- 按每行颜色追踪边界，保留突出角及不齐外框，减少不必要的整条黑带重复。
- 修复一张待定位扫描拦住整批导出的问题；先导出就绪项，显示跳过数量并保留待定位队列。
- 主入口明确为“选择扫描文件夹”，说明包含子文件夹；单独选择图片使用“选择照片文件”。
- 扩大真实测试到完整混合目录，包含单幅、双幅、暗场、空白半幅及 JPG/TIFF 两种版本。测试范围和限制见 VALIDATION.md。

### English

- Fixed the regression that treated low-confidence but usable separators as detection failures; keep proposed splits with a review indicator.
- Use multithreshold RGB uniformity to distinguish film gaps from dark photographic backgrounds.
- Follow row-specific separator colours and retain protruding frame corners while reducing unnecessary overlap.
- Export ready scans even when a batch contains unresolved scans; report skips and retain unresolved entries.
- Make **Choose scan folder** the main action and explicitly mention subfolders; **Choose image files** remains a separate action.
- Expanded real-image checks to the complete mixed folder, including single/double frames, dark scenes, blank halves and JPG/TIFF versions. See VALIDATION.md for scope and limitations.

## 0.2.0 — 2026-09-29

### 中文

- 移除自动方向判断及 OpenCV 依赖，仅保留每张照片独立的手动旋转。
- 新增“输出到原文件夹”，按每个输入文件所在目录分别保存。
- 新增原格式、JPG、16-bit TIFF 输出；JPG 质量可调，并明确提示重新编码损失。
- 默认保留全部外边缘，分界附近允许重叠；不明确的分界保留完整预览，等待手动定位。
- 修复 JPG 向内对齐压缩块可能损失边缘的行为，改为向外保边；必要时使用 EXIF 表示旋转。
- 新增中英双语界面与文档、作者署名、MIT 许可证及独立的第三方许可清单。
- Windows 改为内置运行环境的便携包；Mac 与 Windows 包使用相对资源路径。
- 导入文件夹时跳过处理记录对应的输出，避免重复分片。
- 加入 Windows 未测试声明：作者没有 Windows 电脑，Windows 版本尚未经过实际运行测试。
- 增加奇数尺寸、不同采样、全部 EXIF 方向、不齐边框、可变分界及格式转换测试。

### English

- Removed automatic orientation detection and OpenCV; retained independent manual quarter-turn rotation.
- Added saving beside each source file, including batches from multiple folders.
- Added Original, JPG and 16-bit TIFF output modes, adjustable JPEG quality and explicit conversion notices.
- Preserve outer edges and overlap near separators; ambiguous separators require manual positioning.
- Fixed inward JPEG block alignment that could remove edge pixels; use outward expansion and EXIF rotation when needed.
- Added Chinese/English UI and documentation, author credit, the MIT project license and separate third-party notices.
- Bundled the Windows runtime for portable use; runtime resources are resolved relatively.
- Folder imports skip recorded output pairs to prevent repeated splitting.
- Added the Windows testing notice: the author has no Windows computer, and the Windows version has not been tested on Windows.
- Expanded tests for odd dimensions, sampling, EXIF orientations, irregular borders, variable separators and output conversion.

## 0.1.0 — 2026-09-28

### 中文

- 首个本地桌面原型：批量导入、分隔带检测、双图预览、手动裁切和旋转、同格式导出。
- 当时包含传统方向估计，因实际误判较多，已在 0.2.0 移除。

### English

- Initial local desktop prototype with batch import, separator detection, two-photo previews, crop editing, rotation and original-format export.
- Included traditional orientation estimates; removed in 0.2.0 after poor practical accuracy.
