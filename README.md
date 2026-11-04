# Flori KiCad 元件库

个人维护的 KiCad 符号、封装、数据手册和 3D 模型库。

分发设备可使用 [PCM 打包与发布流程](docs/pcm-packaging.md)，
安装方式见[新设备安装说明](pcm/INSTALL_zh.md)。库或打包相关变更推送后自动打包，主分支同时发布 Release，版本号自动生成；普通维护文档修改跳过。

## 库结构与分类

主库文件使用 `Flori_*` 命名，注册到 KiCad 后的库昵称为 `PCM_Flori_*`。
实际文件名和目录名不添加 `PCM_` 前缀。

| 分类 | 符号 | 封装与 3D 模型 |
| --- | --- | --- |
| `IC` | SoC、存储器、接口、电源 IC 和集成传感器 | 使用 `Package` 中的封装 |
| `Package` | 使用 `IC` 或 `Device` 中的符号 | QFN、SOIC、SOT、BGA 等半导体封装 |
| `Device` | 基础器件、分立半导体、保护器件、磁性器件和显示器件 | 对应的器件专用封装 |
| `Connector` | 优先使用 KiCad 官方连接器符号 | 板间、线缆、卡座、插座及外部接口 |
| `Electromechanical` | 开关、编码器、电机和蜂鸣器 | 对应的机电器件封装 |
| `Mechanical` | 安装与机械结构符号 | 安装孔、支柱和安装结构 |

例如，`symbols/Flori_IC.kicad_sym` 注册为 `PCM_Flori_IC`，
`footprints/Flori_Package.pretty` 注册为 `PCM_Flori_Package`。
符号与封装按各自用途分类，不要求两侧分类完全对称。

## 资源管理与设备配置

- 自定义模型独立存放在 `3dmodels/Flori_*.3dshapes/`，分类与所属封装库一致。
- 本地手册存放在 `resources/datasheets/<Manufacturer-or-Series>/`，
  CAD 图纸存放在 `resources/drawings/<Manufacturer>/`。
- 自定义资源通过 `${FLORI_KICAD_DIR}` 引用；官方模型使用 `${KICAD10_3DMODEL_DIR}`。
  有本地手册时优先引用本地文件，没有本地副本时保留在线链接。
- 克隆或移动工作副本后，关闭 KiCad，在仓库根目录运行
  `python tools/configure_library.py --register-libraries`，配置资源根目录、
  并将 Flori 主库注册到当前设备的库表。

具体规则见[资源维护与 PCM 路径映射](resources/README.md)。
多台开发机频繁修改库时，按[Git 工作副本维护流程](docs/development-workflow.md)操作。
设备配置和打包等维护入口见[工具说明](tools/README.md)。
自动化维护约定见 [AGENTS.md](AGENTS.md)，打包输入与触发规则统一维护在 `tools/pcm-inputs.json`。
库仅提供 `PCM_Flori_*` 分类，不提供旧名称兼容别名。
导入的上游资源保留各自许可证，详见[授权与来源说明](LICENSES/README.md)。

## 维护约定

- 当前文件格式基线为 KiCad 10，各设备应使用兼容的 KiCad 版本。
- 符号主库为 `Flori_IC`、`Flori_Device`、`Flori_Electromechanical` 和 `Flori_Mechanical`。
- 连接器符号优先使用官方库，本库主要维护自定义连接器封装。
- 封装与模型主库为 `Flori_Package`、`Flori_Device`、`Flori_Connector`、
  `Flori_Electromechanical` 和 `Flori_Mechanical`。
- 新器件和新关联使用 `PCM_Flori_*` ID，日常直接编辑主库，无需维护旧库副本。
- 说明文档使用简体中文。库文件、器件和资源文件使用不含空格的英文名称，
  单个符号与封装尽量遵循 KiCad 官方命名风格。
- IC 符号使用准确料号，或有明确意图的兼容系列名。
- 基础、保护、连接、机电和机械器件在有助于搜索时使用 `Function_PartNumber` 命名。
- 通用阻容和保护器件优先采用官方符号，仅封装特殊时保留本地封装。
- 符号字段尽量使用 KiCad 默认项：`Reference`、`Value`、`Footprint`、`Datasheet`、
  `Description`、`ki_keywords` 和 `ki_fp_filters`。
- `Description` 尽量使用中文，`ki_keywords` 保留英文检索词。
- 库字段中不保存供应商、价格或临时导入元数据。

[Flori 迁移记录](docs/audits/flori-migration-2026-11-04.json)保存旧 ID 和资源路径到当前结构的映射。
更早的审计记录保留当时的名称。上游仓库现为 [Flori-KiCad-Library](https://github.com/flowersauce/Flori-KiCad-Library)，
本地项目目录保持原样，Git 远程地址使用新仓库名。PCM 包标识保持不变，以便已安装设备继续更新。
