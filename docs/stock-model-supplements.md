# 官方封装与补充模型导入说明

2026-11-04 导入了 4 个必要的封装定义和 5 份内容不同的补充模型，未修改 KiCad 官方安装目录。
导入封装所需的资源由本库携带，新设备无需再向官方模型目录手工复制这些文件。

## 使用哪些封装

4 个导入封装均位于 `PCM_Flori_Package`，保留原封装名称：

| 封装 | 原库 | `Flori_Package.3dshapes` 中的模型 |
| --- | --- | --- |
| `QFN-20-1EP_3x3mm_P0.4mm_EP1.65x1.65mm_ThermalVias` | `Package_DFN_QFN` | 同主文件名，扩展名为 `.step` |
| `WSON-8-1EP_6x5mm_P1.27mm_EP3.4x4mm` | `Package_SON` | 同主文件名，扩展名为 `.step` |
| `WSON-8-1EP_8x6mm_P1.27mm_EP3.4x4.3mm` | `Package_SON` | 同主文件名，扩展名为 `.step` |
| `SOT-723` | `Package_TO_SOT_SMD` | 同主文件名，扩展名为 `.step` |

例如，选择 `PCM_Flori_Package:WSON-8-1EP_6x5mm_P1.27mm_EP3.4x4mm`，其模型引用为：

```text
${FLORI_KICAD_DIR}/3dmodels/Flori_Package.3dshapes/WSON-8-1EP_6x5mm_P1.27mm_EP3.4x4mm.step
```

`TMI7003C` 默认引用导入的 QFN-20 ThermalVias 封装。
其他已有工程若仍使用官方库 ID，需要显式选择对应的 `PCM_Flori_Package` 封装，才能使用随库模型。
导入本地定义不会重定向原来的官方库 ID。

## 已有封装与模型变体

- 本库原已有普通 QFN-20 及其独立模型，两者继续保留，没有重复复制普通版本的封装。
- 导入的 ThermalVias 封装使用单独命名的模型文件，两个模型变体互不覆盖。
- 原官方目录中的两个 VQFN-104 路径内容相同，现仅保留一份
  `VQFN-104-1EP_10x10mm_P0.35mm_EP7.5x7.5mm.step`，存放于 `Flori_Package.3dshapes`。
  未找到对应的官方封装，因此没有为它额外创建封装。
- 导入封装仅修改模型 URI，焊盘、图形、模型可见性、缩放、旋转和偏移均保留安装目录中的源状态。
  安装目录中的 QFN-20 ThermalVias 本身就与上游 10.0.7 标签存在丝印和 1 脚标记差异，
  这些已有差异也一并保留。

下载模型的原始 STEP 字节保持不变。
6×5 mm WSON 模型的 STEP 文件头仍写着旧的 8×6 mm 文件名，读取到的坐标范围约为 6×5 mm。
使用导入模型前，应在 KiCad 3D 查看器中确认外形尺寸和方向。本轮未运行自动构建、测试或打包命令。

## 来源与维护记录

- [导入记录](audits/imported-stock-assets-2026-11-04.json)：源文件和目标文件映射、SHA-256、
  模型共用关系、符号引用变更及来源信息。
- [原始检查快照](audits/stock-model-candidates-2026-11-04.json)：导入前，相比官方标签多出的 6 个模型路径。
- [Flori 迁移记录](audits/flori-migration-2026-11-04.json)：当前路径和 ID；更早的导入记录保留重新分类前的名称。
- [上游授权说明](../LICENSES/README.md)：保留的 KiCad 署名和许可证。
- [开发维护流程](development-workflow.md)：源码配置与日常更新。

最初的检查依据文件名比较，不能发现所有“以官方同名文件覆盖原模型”的情况。
以后发现此类资源时，可逐项收录模型，并仅复制需要修改资源引用的必要封装。
