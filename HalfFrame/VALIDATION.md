# 检查记录 / Validation record

HalfFrame 0.2.1 · J.C. Lu · 2026-09-30

## 中文

真实输入范围是用户指定的完整扫描目录，包含 522 个原始 JPG/TIFF 文件、8 个子目录；另外 76 个已有导出文件通过处理记录排除。读取失败为 0。同一照片的 JPG 和 TIFF 两个文件分别计数。

以下统计的是“给出可导出分片的文件数”，**不是独立标注的准确率**。目录混合了单幅、双幅、错位跨帧、空白半幅和全黑场景。不能把没有必要拆分的单幅文件按中线强切后算成识别成功。

| 子目录 | 输入文件数 | 0.2.0 可分片 | 0.2.1 可分片 |
|---|---:|---:|---:|
| 00015660 | 72 | 0 | 0 |
| 00015662 | 78 | 28 | 44 |
| 118312/00046508 | 79 | 0 | 0 |
| 118312/00046509 | 79 | 0 | 0 |
| 15033 | 36 | 25 | 35 |
| 15034 | 36 | 29 | 35 |
| 31728 | 68 | 0 | 0 |
| 31729 | 74 | 32 | 71 |

0.2.1 共给出 185 个文件的分片；0.2.0 为 114 个。检查了全目录缩略预览及暗场等重点病例。仍需人工复核的文件保留完整预览；批量导出跳过这些项目并在状态栏显示数量，不再拦住整批。

454 项自动回归检查全部通过，包含 TIFF 像素/位深、JPG 向外保边、全部 EXIF 方向、手动旋转、噪声与亮度渐变、暗场分隔带、不齐边缘和短小突出角、极小图片、格式转换、重名保护、文件夹重复导入和混合队列导出。最初提供的两张照片完成真实界面导出；原格式与 16 位 TIFF 的 8 张结果逐像素比对通过。

Mac 应用移动到含中文和空格的目录后，在不包含开发工具的 PATH 下完成离线自检及界面启动；105 个原生二进制文件未发现开发机绝对路径依赖，签名校验通过。Windows 包的 168 个原生文件均为 x64，资源路径检查通过。

主按钮及中英文提示已验证，明确要求选择文件夹并包含子文件夹；选择照片文件为独立入口。

**作者没有 Windows 电脑，因此 Windows 版本尚未经过实际运行测试。** Windows 包只检查文件结构、x64 组件和相对路径。Mac 包使用本地临时签名，并非 Apple 公证。自动识别不能保证适用于每张照片；应检查预览。

## English

The complete requested scan directory was read: 522 original JPG/TIFF files across eight subfolders, excluding 76 recorded output files. No original failed to load. JPG and TIFF versions of the same photograph are counted as separate files.

The table reports files with usable proposed splits, **not independently annotated detection accuracy**. The corpus mixes single frames, paired frames, misaligned scans, blank halves and dark scenes. Version 0.2.1 proposes splits for 185 files, compared with 114 in 0.2.0. Unresolved files retain full-scan previews and remain in the queue; batch export skips and reports them while exporting ready files.

All 454 regression checks passed, covering pixels/bit depth, outward JPEG cropping, EXIF transformations, manual rotations, grain/shading, dark scenes, irregular edges and small frame tips, tiny images, conversions, name collisions, folder reimports and mixed-batch export. The two original examples were exported through the actual interface; all eight Original/16-bit TIFF outputs passed full-pixel comparison. Folder/file buttons and both interface languages were checked.

The Mac app passed its offline self-test and GUI startup after relocation to a directory containing Chinese characters and spaces, with development tools removed from PATH. All 105 native binaries were checked for developer-path dependencies, and signature validation passed. The Windows package contains 168 x64 native files; resource-path checks passed.

**The author does not have a Windows computer, so the Windows version has not been tested on Windows.** Only package structure, x64 components and relative paths are checked. The Mac app is signed ad hoc, not notarized by Apple. Inspect previews; detection is not guaranteed for every image.

## 0.2.2 发布材料检查 / Release-material checks

2026-09-30：458 项回归检查全部通过（含 4 项 Windows 首次条款确认的模拟检查）。三个 Qt/PySide 源码归档均与官方 SHA-256 相符。中英界面的 10 个许可文档页面均可离线打开。检测与裁切算法保持 0.2.1；前述 522 原图统计沿用其记录，本次未重复整目录图像分析。

2026-09-30: All 458 regression checks passed, including four simulated Windows runtime-acknowledgement checks. The three source archives match official SHA-256 values. All ten document pages open offline in both UI languages. Detection/cropping are unchanged from 0.2.1; the 522-file corpus figures above are retained from that validation, not a new corpus run.

0.2.2 Mac 包另通过中文/空格路径移动后的离线自检与界面启动；105 个原生二进制未发现开发机绝对加载路径。以独立上游 arm64 QtCore 替换测试副本中的库并本地重新签名后，界面启动和导出自检再次通过。此验证使用兼容上游库，不声称已经编译任意用户修改的 Qt 源码。

The 0.2.2 Mac bundle passed relocated offline self-test and GUI startup; 105 native binaries have no developer-specific absolute loader paths. Replacing QtCore in a test copy with an independently copied compatible upstream arm64 library, then ad-hoc re-signing, passed GUI startup and export self-tests again. This is a replacement test using an upstream library, not a claim to have compiled arbitrary user modifications.
