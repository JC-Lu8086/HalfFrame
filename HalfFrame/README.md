# 半格 · HalfFrame

**作者 / Author: J.C. Lu**  
**版本 / Version: 0.2.2**  
**许可证 / License: MIT（项目自身代码 / application's own code）**

## 中文

把一张含两幅半格照片的扫描图分成两张照片。支持批量导入 JPG/JPEG/TIF/TIFF、横向或竖向扫描、独立手动旋转、分隔线和四边微调。界面左侧可切换中文与 English。

### 直接运行

- **Mac：** Apple Silicon（M 系列），macOS 14 或更新系统。打开 `HalfFrame.app`。所需环境已内置，不需要安装 Python 或下载模型。
- **Windows：** Windows 10/11 x64。便携版完整解压并双击 `HalfFrame.cmd`。内置 Python 和运行库，不需要安装依赖。不要只取出启动文件；请保留整个文件夹。**作者没有 Windows 电脑，因此 Windows 版本尚未经过实际运行测试。** 此包仅完成文件结构及路径检查，不能保证在所有 Windows 环境下正常运行。
- 处理过程完全离线。移动整个应用或便携文件夹不需要修改任何路径。
- 这是未由商业证书签名的应用，系统可能显示常规的来源确认。不同 CPU 架构需要对应构建；当前不宣称支持 Intel Mac、Windows ARM 或旧版系统。

### 操作

1. 点击绿色“选择扫描文件夹”按钮，选择**文件夹**；程序会读取该目录及子文件夹内的 JPG/TIFF。只导入部分照片时，使用“选择照片文件”。也支持拖入。
2. 程序寻找帧间黑带或亮带。两张照片均保留输入的显示方向；**自动回正已完全移除**。需要时分别点左转/右转。
3. 检查预览，调整分界。默认保留全部外边缘，在分界附近重叠保边；不是按固定宽度裁掉中间一条。
4. 勾选“输出到原文件夹”，或选择另一个文件夹。多目录导入时，该选项分别保存到每张原片所在目录。
5. 选择输出格式，导出当前图片或整个队列。文件名增加 `_1`、`_2`，重名自动加序号，绝不覆盖原片。

再次导入文件夹时，会跳过有效处理记录指向的本软件输出，避免重复分片；直接选择具体图片仍可导入。请保留输出旁的处理记录。

### 输出格式

| 选项 | 行为 |
|---|---|
| 原格式 | TIFF 保留像素位深并无损保存；JPG 直接裁切压缩数据，不二次有损编码。 |
| JPG | 生成 8-bit JPG，质量可设 1–100（默认 95），会重新有损编码；16-bit 会降低到 8-bit，透明区域合成白色。 |
| 16-bit TIFF | 使用无损压缩。16-bit 输入保留原值；8-bit 输入按 `值 × 257` 精确映射到 16-bit，不会增加原片细节。 |

原格式 JPG 的裁切边界只向外扩展到压缩块边界，不向内丢像素。若边缘有不完整压缩块，保留编码像素并使用 EXIF 方向标签表示手动旋转；看图软件须支持 EXIF 方向。

作者署名属于软件，不会加到照片画面上，也不会把照片的作者/版权字段改成软件作者。常见 ICC、分辨率、描述信息会按输出格式保留；旧缩略图、结构化尺寸描述、XMP、厂商私有元数据不保证保留。格式转换会产生新的文件和相应元数据。

### 保留画面与适用范围

默认两个输出框合起来覆盖整个扫描，不自动剪掉不齐的外框。分界倾斜、宽度变化或局部凸出时，宁可保留更多边框或少量重复区域。低评分但仍有明确分隔带时会给出分片并提示复核；确实找不到分界或有多个竞争分界时，保留两张全幅预览并要求手动定位。批量导出会先处理已定位的扫描，跳过待定位项并显示数量；待定位项留在队列。自动识别不能保证每种拍摄内容都判断正确，请检查预览。主动缩小外边界属于你手动指定的裁切。

支持单页 8/16-bit 无符号整数灰度、RGB、RGBA TIFF，以及常见 JPEG。多页、浮点、CMYK TIFF 暂不支持。旋转仅为 90° 的整数倍，不拉伸、不任意角度插值、不自动调色。大图仍需要与像素数量相应的内存，但按张处理，不同时载入整批原始像素。

### 源码、版本与许可

- 完整应用源码、测试与构建脚本随源码包提供，Mac 包内也保留 `Contents/Resources/source`。
- [版本记录](CHANGELOG.md) / [MIT 完整文本](LICENSE) / [第三方许可与审查范围](THIRD_PARTY_NOTICES.md)。
- 项目自身代码以 MIT 提供，可使用、修改和再分发，但须保留版权及许可声明。第三方组件仍归其原作者，遵循各自许可证，并非全部为 MIT。
- 本包附带应用源码和构建信息，方便修改与重建；MIT 本身不要求公开衍生应用源码。Qt/PySide/Shiboken 使用 LGPLv3 的动态库许可路径，发布时仍须满足库的对应源码、通知、替换及重新链接义务，详细说明见第三方声明。

## English

**HalfFrame by J.C. Lu** splits full-frame scans containing two half-frame photographs. It supports batch JPG/JPEG/TIF/TIFF imports, portrait or landscape scans, independent manual rotation, and editable crop bounds. Switch the interface between Chinese and English from the language selector.

### Run without installation

- **Mac:** Apple Silicon, macOS 14 or later. Open `HalfFrame.app`; Python and libraries are bundled.
- **Windows:** Windows 10/11 x64. Extract the complete portable folder and double-click `HalfFrame.cmd`. Python and libraries are included; keep the complete folder together. **The author does not have a Windows computer, so the Windows version has not been tested on Windows.** Only package structure and paths have been checked; operation in every Windows environment is not guaranteed.
- Processing is offline. Moving the complete app/folder does not require changing paths. No model or cloud service is used. Intel Macs, Windows ARM and older operating systems are not claimed as supported by these binary packages.
- The app is not commercially signed; the operating system may show a normal publisher/origin prompt.

### Workflow and output

Use the green **Choose scan folder** button to select a folder; images in subfolders are included. Use **Choose image files** for individual selections. Inspect the previews, rotate each photograph manually as needed, and export. **Automatic orientation detection has been completely removed.** Choose a destination folder or save beside each source file. Existing files are never overwritten; duplicate names receive a suffix. Folder imports skip local exported pairs identified by valid processing records, preventing repeated splitting. Explicitly selected image files remain importable; keep the processing records beside the exports.

| Output | Behavior |
|---|---|
| Original | TIFF retains original bit depth and pixel values. JPEG crop/rotation avoids another lossy encoding. |
| JPG | Re-encodes to 8-bit JPEG at quality 1–100, default 95. This is lossy; 16-bit precision is reduced, and transparency is composited on white. |
| 16-bit TIFF | Lossless output. Existing 16-bit values are retained; 8-bit values are mapped exactly by multiplying by 257. This does not create additional image detail. |

The default rectangles retain every source edge and overlap around the separator. Uneven or slanted borders may retain more border or duplicate content. Low contrast with a usable separator gives a proposed split marked for review. Missing or competing separators keep full-scan previews and require manual positioning. Batch export processes ready scans and reports skipped unresolved scans, which remain in the queue. The detector is not a guarantee of correct boundaries for every scene; inspect the preview. Explicit manual changes to outer crop bounds are your chosen cropping operation.

For original JPEG output, bounds expand outward to compression-block boundaries. Partial edge blocks are retained; where a physical lossless rotation cannot preserve them, the selected rotation is written to EXIF. The viewer must honor EXIF orientation.

The software author credit is not a photo watermark and does not replace the photograph's creator/copyright fields. Common ICC, resolution and descriptive metadata are retained where supported; stale thumbnails, structured dimensions, XMP and private vendor fields are not guaranteed to survive. Conversion creates new output metadata.

Supported TIFF inputs are single-page unsigned 8/16-bit grayscale, RGB or RGBA. Multipage, floating-point and CMYK TIFF are not supported. Rotations are quarter-turns only; no arbitrary-angle interpolation, stretching or automatic color correction is applied.

### Open source and development

Copyright (C) 2026 **J.C. Lu**. The application's own code is licensed under **MIT**, permitting use, modification and redistribution while retaining the copyright and license notice. Third-party components retain their original copyrights and licenses; they are not all MIT. See [LICENSE](LICENSE), [CHANGELOG](CHANGELOG.md), and [THIRD_PARTY_NOTICES](THIRD_PARTY_NOTICES.md).

Application source, tests and build scripts are included to support modification and rebuilding. MIT itself does not require publishing derivative application source. Qt/PySide/Shiboken use the LGPLv3 dynamic-library option; distributors must still fulfill applicable library-source, notice, replacement and relinking obligations. The included review is a bounded dependency audit, not a legal certification.

```sh
python -m venv .venv
# Activate the virtual environment, then:
python -m pip install -r requirements-release.txt
python app.py
python -m pip install pytest pyinstaller
python -m pytest tests -q
python build.py
```

Development builds need `jpegtran` on PATH or in the project's `bin` directory. End-user packages include it. Build macOS apps on macOS and Windows executables on Windows; `build_windows_portable.py` can assemble the portable Windows folder from official embedded Python and Windows wheels.

This software is based in part on the work of the Independent JPEG Group.

## 0.2.2 发布材料 / Release materials

项目自编代码采用 MIT；第三方代码保留各自许可。本版本实际附带 Qt/PySide/Shiboken 对应源码及校验值，见 `third_party_sources/`；库替换与重建见 `RELINKING.md`，发布范围见 `RELEASE-LICENSING.md`。应用内可点击“开源许可与第三方声明”离线查看。

当前交付物包括 Mac、Windows 便携版和源码包。发行者已确认接受 Visual Studio Community 许可；Windows 首次启动需主动同意其微软运行库原始条款，仅在本机保存确认。作者仍未在 Windows 实机测试。源码包不夹带 Windows EXE/DLL，Windows 组装时使用 `--jpeg-tools` 指定官方工具目录。

Application code is MIT; dependencies retain their own terms. Qt/PySide/Shiboken source archives and checksums are included in third_party_sources. See RELINKING.md for library replacement and RELEASE-LICENSING.md for distribution scope. The app provides an offline license viewer. Deliverables include the Mac app, Windows portable package and source archive. The publisher confirmed accepting Visual Studio Community licensing; first Windows launch requires agreement to the included Microsoft runtime terms, stored only locally. Windows execution remains untested. Public source contains no Windows EXE/DLL; Windows assembly accepts the official JPEG tools via --jpeg-tools.
