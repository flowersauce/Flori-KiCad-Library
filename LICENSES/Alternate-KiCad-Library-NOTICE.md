# Alternate KiCad Library 来源与授权

`footprints/Flori_Package.pretty/SOT-723.kicad_mod` 的几何来源于 Dawid Cisło 的 Alternate KiCad Library：

- 上游：https://github.com/DawidCislo/Alternate-KiCad-Library
- 原库 ID：`Package_TO_SOT_SMD_AKL:SOT-723`。
- 该资源保留上游 CC-BY-SA 4.0 及电子设计例外，不适用本仓库的 MIT 授权。
- 上游为 KiCad 社区库的衍生作品；许可证与电子设计例外原文见本目录 `KiCad-Libraries-LICENSE.md`，AKL 署名与授权说明见上游 README 的 License 节。
- 本次更改：转换为 KiCad 10 文件格式，删除一条零长度 Courtyard 线段，附加本库既有 STEP 模型引用；保留 AKL 焊盘编号、位置、尺寸及其余图形几何。
- 模型沿用原文件及既有来源记录，其字节、偏移、旋转和缩放未改变；不将 AKL 封装授权自动套用到模型。

详细源文件 SHA-256、目标与模型哈希见 `docs/audits/sot-723-akl-repair-2026-11-15.json`。
