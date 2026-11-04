# Flori PCM 包安装与新设备检查

需要 KiCad 10。主库直接通过 PCM 安装，不需要克隆源码，也不需要配置 `FLORI_KICAD_DIR`。

## 从文件安装

1. 在 KiCad 项目管理器中打开“插件与内容管理器”（Plugin and Content Manager）。
2. 保持库昵称前缀为默认 `PCM_`，启用自动将安装的库加入全局库表。
3. 选择“从文件安装”（Install from File），打开 `Flori-KiCad-Library-<版本>.zip`。
4. 应用待处理变更。若库列表尚未刷新，关闭并重新打开 KiCad。

不要把 GitHub Actions 下载制品的外层 ZIP 直接交给 PCM。
先解压制品，在其中找到真正包含根目录 `metadata.json` 的 Flori 安装包。
同一 KiCad 配置中，一个 `PCM_Flori_*` 昵称只使用一个来源，避免源码注册和 PCM 包重复占用。
已有源码配置的开发机，建议使用独立的 KiCad 配置和 PCM 安装目录测试；无需删除日常库或官方库。

## 在新机器检查

- 符号库应出现 `PCM_Flori_IC`、`PCM_Flori_Device`、`PCM_Flori_Electromechanical`、`PCM_Flori_Mechanical`。
- 封装库应出现 `PCM_Flori_Package`、`PCM_Flori_Device`、`PCM_Flori_Connector`、
  `PCM_Flori_Electromechanical`、`PCM_Flori_Mechanical`。
- 放置 `PCM_Flori_IC:TMI7003C`，确认默认封装指向
  `PCM_Flori_Package:QFN-20-1EP_3x3mm_P0.4mm_EP1.65x1.65mm_ThermalVias`。
- 查看导入的 QFN-20 ThermalVias、两款 WSON-8、SOT-723，检查焊盘与 3D 模型的尺寸、方向和高度。
- 打开 `PCM_Flori_IC:XGZP6859D` 的本地手册，确认资料随包可用。
- 模型和本地资料路径应使用 `${KICAD10_3RD_PARTY}`，不应依赖开发机盘符或源码目录。

建议保留安装包、`.sha256`、版本号和报错日志，便于反馈问题。

## 旧工程兼容配置（按需）

包内包含生成的旧聚合库，因此默认 PCM 注册会提供 `PCM_Flowersauce_*` 昵称。
不带前缀的 `Flowersauce_*` 昵称及 `${FLOWERSAUCE_KICAD_DIR}` 历史资源路径需要额外配置。
仅使用 `PCM_Flori_*` 的新工程无需此步骤。

在 PCM 中打开包目录，进入：

```text
resources/com_github_flowersauce_flori-kicad-library/
```

关闭 KiCad，在该目录使用 Python 3.10 或更高版本运行：

```powershell
python configure_pcm.py --dry-run
python configure_pcm.py
```

没有系统 Python 时，可使用 KiCad 安装目录中的 Python。
自定义 KiCad 配置目录可增加 `--config-dir <版本配置目录>`。
脚本会备份配置文件，仅合并旧别名、设置历史资源变量，并生成本地资源链接；
不修改官方库，也不重定向 `PCM_Flori_*` 主库昵称。

PCM 更新会替换包目录。依赖旧别名或历史资源路径的工程，更新后重新运行兼容脚本。
资源链接优先使用硬链接，无法建立时退回复制，兼容资源按只读使用。

若安装失败或显示异常，请反馈版本、KiCad 版本、库昵称、错误信息及有问题的器件 ID。
