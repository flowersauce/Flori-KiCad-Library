# 导入资源的授权与来源

[导入记录](../docs/audits/imported-stock-assets-2026-11-04.json)所列上游资源保留原有上游许可证，
不改用本仓库的 MIT 许可证。

- 4 个复制的封装定义来源于 KiCad 元件库。
  仅调整模型 URI，保留安装目录中源封装的几何和模型变换参数；
  原库 ID、来源链接及哈希均已记录。
- [KiCad-Libraries-LICENSE.md](KiCad-Libraries-LICENSE.md)是未经修改的上游授权原文，
  包含 KiCad 元件库例外条款。
- STEP 文件按原始字节复制，保留文件头中的授权声明。
  导入记录区分了明确写在文件头中的许可证与未记录原始下载来源的文件。

导入记录保留导入时使用的路径，当前路径和 ID 见[Flori 迁移记录](../docs/audits/flori-migration-2026-11-04.json)。
生成的兼容副本保留相同的上游署名信息。
