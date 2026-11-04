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

本库只提供 `PCM_Flori_*` 分类，不包含旧名称兼容库或安装后配置脚本。
