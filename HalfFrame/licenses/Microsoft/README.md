# 微软运行库分发记录 / Microsoft runtime distribution record

来源：官方 CPython 3.12.10 嵌入包，以及 NumPy 2.5.3、PySide6-Essentials 6.11.2、Shiboken6 6.11.2 的 Windows wheels。runtime-provenance.json 逐文件记录原归档成员与 SHA-256，并确认文件内容未修改。未从个人电脑的系统目录复制 DLL。

Python-CRT-conditions.txt 为 CPython 所附的 Windows 条件；完整原文另保留于 ../Python-Windows-LICENSE.txt。Visual-Studio-2022-Community-License-EN.docx 从微软官方许可页下载，TXT 是逐段提取的阅读副本，以 DOCX 原文为准；仅用于核对条款，不代表作者已接受或已获得该产品许可。

官方来源：
- https://raw.githubusercontent.com/python/cpython/v3.12.10/PC/crtlicense.txt
- https://visualstudio.microsoft.com/license-terms/vs2022-ga-community/
- https://visualstudio.microsoft.com/wp-content/uploads/2021/11/Visual-Studio-2022-Community-License-EN.docx
- https://learn.microsoft.com/en-us/visualstudio/releases/2022/redistribution
- https://learn.microsoft.com/zh-cn/cpp/windows/redistributing-visual-cpp-files?view=msvc-170

发行者已确认持有并接受 Visual Studio Community 许可。本次记录依据其确认，并不独立认证账号、资格或具体产品版本，也未替发行者接受任何协议。

已从微软官方 Visual C++ 2015–2022 运行库安装包提取原始中英条款（未执行安装包），保留 RTF 与便于阅读的 TXT。来源、安装包及条款哈希见 runtime-terms-provenance.json。程序在 Windows 首次启动时展示原文并要求主动确认；记录仅存本机用户设置。终端用户条款仅适用于微软组件，不限制 HalfFrame MIT 或 Qt LGPL 权利。其他再分发者仍须具备相应权利。

English: The publisher confirmed holding and accepting Visual Studio Community licensing. This records that declaration without independently authenticating entitlement, account or product version, and without accepting an agreement on their behalf. Original English/Chinese runtime terms were extracted from Microsoft's official Visual C++ 2015–2022 installer without executing it; original RTF and readable TXT copies are included. Provenance and hashes are recorded. First Windows launch requires affirmative local acknowledgement. These terms apply only to Microsoft components, not HalfFrame MIT or Qt LGPL code; further distributors need applicable authority of their own.
