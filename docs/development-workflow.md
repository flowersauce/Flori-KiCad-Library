# Flori 多设备开发与发布维护

## 开发机使用 Git 工作副本

经常编辑库的设备保留一份位置稳定的工作副本，由 KiCad 直接读取。
不同设备的目录可以不同：`FLORI_KICAD_DIR` 提供本机根路径，库昵称和资源相对路径保持一致。

新开发机按以下步骤配置：

1. 安装兼容的 KiCad 10，并初始化标准库。
2. 将仓库克隆到计划长期使用的目录。
3. 关闭 KiCad，在仓库根目录运行：

   ```powershell
   python tools/configure_library.py --register-libraries
   ```

4. 打开 KiCad。符号主库为 `PCM_Flori_IC`、`PCM_Flori_Device`、
   `PCM_Flori_Electromechanical` 和 `PCM_Flori_Mechanical`；
   封装主库为 `PCM_Flori_Package`、`PCM_Flori_Device`、`PCM_Flori_Connector`、
   `PCM_Flori_Electromechanical` 和 `PCM_Flori_Mechanical`。

脚本同时注册旧 `Flowersauce_*` 和 `PCM_Flowersauce_*` 别名、刷新兼容文件，并设置两个资源变量。
`FLORI_KICAD_DIR` 指向仓库根目录，`FLOWERSAUCE_KICAD_DIR` 指向其 `compat` 目录。
其他已注册库保持原样，修改配置前会生成备份。可用 `--dry-run` 预览。
此流程不修改 KiCad 官方安装目录中的文件。

实际库文件名使用 `Flori_*`；`PCM_Flori_*` 是脚本注册的昵称，不要将 `PCM_` 再加到文件名上。

## 多设备日常更新

1. 切换版本或设备前，保存并关闭相关库编辑器，避免旧的内存副本覆盖新拉取的内容。
2. 编辑前检查工作区。在本地修改已经提交或妥善保存的前提下，用 `git pull --ff-only` 更新共享分支。
3. 编辑 `symbols/Flori_*`、`footprints/Flori_*` 及其外置资源。
   保存到库后，刷新兼容文件：

   ```powershell
   python tools/sync_compat.py
   ```

4. 检查差异，将主库修改与发生变化的 `compat/symbols`、`compat/footprints` 生成文件一起提交并推送。
5. 在另一台设备拉取后，重新加载相关库编辑器或选择器。
   如果旧工程仍引用历史资源路径，在拉取模型或资料更新后运行同一刷新命令，更新本地链接。

相互依赖的符号、封装和模型尽量放在同一次提交中。
在设备间交换提交后再继续编辑同一 `.kicad_sym`，避免两边各自修改而产生分歧。
发生分歧时显式解决，不在同步过程中直接丢弃本地修改。

主库直接读取工作副本，更新器件或在已有分类内新增条目，无需重新安装或发布包。
新增整个 `.kicad_sym` 或 `.pretty` 分类、移动工作副本或使用新 KiCad 配置时，再运行注册脚本。
注册可重复执行，也会刷新兼容数据。

新设计使用主库昵称。旧别名覆盖 [library-layout.json](../tools/library-layout.json) 中记录的历史成员，
新器件不必加入这些旧目录。生成的 `compat/` 文件按只读使用，详见[兼容层维护](../compat/README.md)。

Git 更新不会自动改写原理图或 PCB 内已经保存的器件副本。
按需使用“从库更新符号”（Update Symbols from Library）、
“从库更新封装”（Update Footprints from Library）或“更换封装”（Change Footprints），并检查所选变更。

## 主要使用库的设备采用 PCM 发布版

PCM 用于分发带标签的版本快照，适合主要放置器件、按发布版本更新的设备。
修改仍在 Git 工作副本中完成，再由源码生成发布包。
直接编辑安装后的包会形成另一份修改来源，包更新时可能被替换。

开发机上，每个 `PCM_Flori_*` 昵称只选择一个来源。
源码配置与 PCM 安装使用同一组主库 ID，避免同时让发布版和工作副本占用同一个库表条目。

PCM 昵称前缀保持默认 `PCM_`。
打包、路径转换及旧别名兼容方案见 [PCM 打包与发布](pcm-packaging.md)。
源码配置脚本不会构建、发布或安装 PCM 包。

## 仓库名称与本地目录

上游仓库名、本地工作副本目录和 KiCad 库昵称互相独立。
当前上游为 `flowersauce/Flori-KiCad-Library`，不必重命名或重新克隆本地目录。
已有设备更新远程地址可执行：

```powershell
git remote set-url origin git@github.com:flowersauce/Flori-KiCad-Library.git
```

只要工作副本位置不变，本机资源变量仍然有效。

参考：[KiCad 路径变量](https://docs.kicad.org/10.0/en/kicad/kicad.html#_paths_and_libraries_configuration)、
[更新 PCB 封装](https://docs.kicad.org/10.0/en/pcbnew/pcbnew.html#_updating_and_exchanging_footprints)、
[更新原理图符号](https://docs.kicad.org/10.0/en/eeschema/eeschema.html#_updating_and_exchanging_symbols)。
