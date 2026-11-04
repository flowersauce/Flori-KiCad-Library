# 元件库资源维护

自定义模型和本地资料均作为独立文件维护。符号与封装通过 `${FLORI_KICAD_DIR}` 引用资源，
该变量指向当前仓库根目录。每台设备只需配置一次根路径，器件中不逐项保存机器绝对路径。

## 目录结构

```text
3dmodels/
  Flori_Package.3dshapes/
  Flori_Device.3dshapes/
  Flori_Connector.3dshapes/
  Flori_Electromechanical.3dshapes/
  Flori_Mechanical.3dshapes/
resources/
  datasheets/<Manufacturer-or-Series>/<PartNumber>[_Document-or-Revision].pdf
  drawings/<Manufacturer>/<PartNumber>.dwg
```

目录占位项依次表示厂商或系列、料号，以及可选的文档类型或修订版本；实际名称使用英文。

- [自定义 3D 模型](../3dmodels/)：分类与封装库一致。
- [数据手册](datasheets/)：手册、产品简介和厂商承认书。
- [CAD 图纸](drawings/)：可编辑或供参考的 DWG 图纸。
- [资源外置记录](../docs/audits/resource-migration-2026-11-04.json)：原文件名、嵌入附件来源、
  SHA-256 和引用变更。此文件属于历史记录，日常更新不需要修改。
- [Flori 分类与命名迁移记录](../docs/audits/flori-migration-2026-11-04.json)：新旧库 ID、分类及模型路径映射。
  较早审计记录中的文件名表示当时的状态。

## 配置一台设备

需要 KiCad 10 和 Python 3.10 或更高版本。修改配置前先关闭 KiCad。
克隆或移动工作副本后，在仓库根目录运行：

```powershell
python tools/configure_library.py --register-libraries
```

脚本配置以下资源变量：

| 变量 | 值 | 用途 |
| --- | --- | --- |
| `FLORI_KICAD_DIR` | 仓库根目录 | 当前主库和资源 |

使用 `--register-libraries` 时，脚本将发现的 `Flori_*` 文件注册为 `PCM_Flori_*`，
不注册旧名称或别名。
其他库和设置保持原样，发生修改的配置文件会先备份。新设备应先完成 KiCad 标准库初始化。

不使用 `--register-libraries` 时，只配置资源变量，不修改库表注册。
`--dry-run` 用于预览，不写入文件；自定义配置位置可使用
`--config-dir <versioned-profile-directory>`。KiCad 自带的 Python 也可以运行这些脚本。
此流程配置的是源码工作副本，不会安装 PCM 发布包。

可在“首选项 → 配置路径”（Preferences > Configure Paths）中查看变量。
同名操作系统环境变量优先于 KiCad 配置；存在冲突时，需要单独修改外部变量。

## 新增或更新模型

1. 将自定义模型放入与封装库对应的 `.3dshapes` 目录。
2. 优先使用封装文件的主文件名及小写 `.step` 扩展名。
   不同高度或不同装配状态使用有明确含义的后缀。
3. 在封装的 3D 模型设置中填写变量路径，例如：

   ```text
   ${FLORI_KICAD_DIR}/3dmodels/Flori_Electromechanical.3dshapes/Buzzer_5x5mm_SMD.step
   ```

4. 仅替换文件引用时，保留原有缩放、旋转、偏移和模型可见性，
   并在 KiCad 3D 查看器中确认更新后的模型。
5. 已随 KiCad 安装的官方模型通过 `${KICAD10_3DMODEL_DIR}` 引用。

可复用的库定义采用外置资源；需要自包含交付时，可在工程归档中使用嵌入资源。
不使用依赖编辑器或工程上下文的裸 `../` 路径。`${KIPRJMOD}` 指向当前工程，不是此共享库。

现有未被引用的模型变体仍保留。带 `_Source_<hash>` 后缀的文件与同名来源的另一副本内容不同，
应比较后再决定替换或删除哪一份。

## 新增或更新数据手册

1. 使用 ASCII 厂商目录；厂商不明确时可使用便于识别的系列名。
   文件名包含料号，以及必要的文档类型或修订版本。
2. 新资源使用小写 `.pdf` 或 `.dwg` 扩展名，文件名不含空格。
3. 有本地文件时，在 `Datasheet` 字段中使用变量路径，例如：

   ```text
   ${FLORI_KICAD_DIR}/resources/datasheets/CFSensor/XGZP6859D.pdf
   ```

4. 没有本地副本时，保留在线链接。新增器件优先使用稳定的厂商文档链接，是否下载本地副本按需决定。
5. 符号和封装使用同一文档时共用一个文件；不同修订版和模型变体分别保存。

在线链接优先采用厂商 PDF 或官方文档页。移除已知跟踪参数，例如 `lcsc_vid`、`spm`、
`ts`、`ref_url` 和 `utm_*`；保留下载所需的文档标识，例如东芝的 `did`，
以及矽力杰的 `id`、`ftype` 和 `type`。实际文件名中的编码空格和非 ASCII 字符不能直接删去。

HTTP 403 可能只是限制自动访问；HTTP 200 也可能返回 HTML 错误页，而非 PDF。
只有确认替换链接属于正确厂商和文档后，才替换原有可用链接。
[链接整理记录](../docs/audits/datasheet-links-2026-11-04.json)保存了当次修改及有限范围的 HTTP 检查结果。

曾放入 KiCad 安装目录的下载模型，参见[官方封装与补充模型导入说明](../docs/stock-model-supplements.md)。
日常 Git 更新和重新注册时机见[开发维护流程](../docs/development-workflow.md)。

## PCM 打包

仓库是可编辑的资源来源。PCM 会将不同内容安装到不同根目录，因此打包时需要转换源码中的路径前缀：

| 源码前缀 | PCM 包中的前缀 |
| --- | --- |
| `${FLORI_KICAD_DIR}/3dmodels/` | `${KICAD10_3RD_PARTY}/3dmodels/<package_id_with_underscores>/` |
| `${FLORI_KICAD_DIR}/resources/` | `${KICAD10_3RD_PARTY}/resources/<package_id_with_underscores>/` |

转换在打包暂存副本中进行，源码继续使用开发变量，包内包含实际引用的模型和资料。
PCM 库昵称前缀保持默认 `PCM_`，使 `Flori_*` 文件安装后得到与源码配置相同的 `PCM_Flori_*` ID。

源码配置脚本不会构建或发布包。独立构建器与 GitHub Actions 负责生成元数据、转换包内路径，
只分发当前 Flori 主库，详见 [PCM 打包与发布](../docs/pcm-packaging.md)。

参考：[KiCad 路径配置](https://docs.kicad.org/10.0/en/kicad/kicad.html#_paths_and_libraries_configuration)、
[PCM 打包规范](https://dev-docs.kicad.org/en/addons/index.html)、
[KiCad 数据手册 URI 解析](https://github.com/KiCad/kicad-source-mirror/blob/10.0/common/eda_doc.cpp)。
