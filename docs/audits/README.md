# 来源与迁移审计

本目录保存资源外置、在线链接整理、官方资源补充和 Flori 分类迁移的原始记录。
其中的旧名称和 `backup` 字段记录当时的状态；对应临时备份已经清理，不再作为可用路径。

新旧 ID、资源映射和 SHA-256 仍用于追溯，不因临时文件清理而删除。
PCM 构建器读取导入记录和 Flori 迁移记录，移除临时备份字段后随包保留授权来源。

## XUNPU XH2.54 贴片封装

2 位和 4 位变体使用 [KiCad Library Tools 的 KicadModTree](https://gitlab.com/kicad/libraries/kicad-library-tools/-/tree/090252c1f2429ceb8bd8ef2aa466b6c135f6273a) 及定制配方生成。各封装的 `Datasheet` 指向厂商图纸，图纸版本和页码见封装描述。

- 两款 PWT 图纸只标注两排焊盘的相对位置。对齐本体时，将固定焊盘沿插接方向对中到图示 3.00 mm 长的焊接片。固定焊盘的铜皮超出本体前缘 0.45 mm，定位板边时需另计铜到板边的间距。侧边丝印沿主壳体绘制，侧翼可能局部遮挡丝印。
- 图纸未标 1 脚。四款封装按从 PCB 正面看由左至右编号。两款侧插封装的插接面朝 KiCad 的 +Y 方向。
- 四款 STEP 从维护者提供的 `3D_PCB1_2026-11-23.step` 中提取，来源为嘉立创 EDA 专业版 PCB 导出。保留来源文件头，去除导出标识、统一颜色并将安装坐标对齐到对应 Flori 封装。原模型作者和具体许可未记录，仓库 MIT 授权不适用于这些第三方模型。

## HANBO WAFER-XH254Z 立式直插

- 共用封装位于 `PCM_Flori_Connector`。2P 为 `HANBO_WAFER-XH254Z_1x02_P2.50mm_Vertical`，4P 为 `HANBO_WAFER-XH254Z_1x04_P2.50mm_Vertical`。原点均为 1 脚中心。
- 以 KiCad Footprints `10.0.0` 的 [JST XH 2P](https://gitlab.com/kicad/libraries/kicad-footprints/-/blob/10.0.0/Connector_JST.pretty/JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical.kicad_mod) 和 [JST XH 4P](https://gitlab.com/kicad/libraries/kicad-footprints/-/blob/10.0.0/Connector_JST.pretty/JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical.kicad_mod) 为底稿。保留原焊盘、丝印与庭院，校正 `F.Fab` 轮廓并绑定汉博模型。封装沿用 [KiCad 元件库授权](../../LICENSES/KiCad-Libraries-LICENSE.md)。
- 按[汉博 WAFER-XH254Z-NAX 机械图 Rev A4 第 1 页](https://atta.szlcsc.com/upload/public/pdf/source/20240628/5F265ED5DCD1AB9F6070F992FAF53820.pdf)中的 PCB Layout 与尺寸表，孔距为 2.50 mm，2P、4P 外壳分别为 7.50 × 5.80 mm、12.50 × 5.80 mm。两款封装保留标准底稿的 Ø1.00 mm 和 Ø0.95 mm 成品孔径。图纸标注 Ø0.80 mm，公差 +0.10/0 mm，进一步收紧前需用实际样品验证。
- 六份 STEP 由维护者提供的 `3D_PCB1_2026-11-24.step` 中两个嘉立创 EDA 导出模型整理而成。去除外壳上的导出标识并恢复平面，塑壳按商品照片近似配色，保留针脚几何、原色及来源文件头。原模型作者和具体许可未记录，仓库 MIT 授权不适用于这些 STEP。
- 每个封装预置三色模型，安装坐标一致。默认只显示米色 `AM`，可在 PCB 的“封装属性 → 3D 模型”中切换“显示”勾选，每次只显示一种颜色。采购字段按实际选用的完整料号与立创编号填写。

| 颜色 | 2P 料号 | 立创编号 | 4P 料号 | 立创编号 |
| --- | --- | --- | --- | --- |
| 米色 | `WAFER-XH254Z-2AM` | [C22751822](https://item.szlcsc.com/24478757.html) | `WAFER-XH254Z-4AM` | [C22751824](https://jlcpcb.com/partdetail/HanboElectronic-WAFER_XH254Z4AM/C22751824) |
| 红色 | `WAFER-XH254Z-2AH` | [C22751786](https://www.lcsc.com/pl/product-detail/C22751786.html) | `WAFER-XH254Z-4AH` | [C22751788](https://jlcpcb.com/partdetail/HanboElectronic-WAFER_XH254Z4AH/C22751788) |
| 蓝色 | `WAFER-XH254Z-2AL` | [C22751795](https://www.lcsc.com/it/product-detail/C22751795.html) | `WAFER-XH254Z-4AL` | [C22751797](https://item.szlcsc.com/24478732.html) |
