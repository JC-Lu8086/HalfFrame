# JPEG 工具 / JPEG tools

公开源码包不包含 Windows EXE/DLL。Mac 构建使用构建机安装的 libjpeg-turbo/jpegtran，并将所需工具打入应用。Windows 构建通过 `--jpeg-tools` 指向官方 libjpeg-turbo 3.2.0 x64 工具目录（jpegtran.exe、jpeg62.dll）。来源和校验记录见 ../licenses/libjpeg-turbo-windows/PROVENANCE.md；二进制发布还需满足相应运行库条件。

The public source archive contains no Windows EXE/DLL. Mac builds collect the installed jpegtran tool. Windows builds accept official libjpeg-turbo 3.2.0 x64 jpegtran.exe and jpeg62.dll through --jpeg-tools; provenance is retained in the license folder.
