# Flori 包内资源的授权与来源

本包包含采用不同许可证的资源，不将第三方资源统一改为 MIT 授权。

- `licenses/LICENSE`：仓库原有的 MIT 授权原文。
- `licenses/KiCad-Libraries-LICENSE.md`：KiCad 元件库授权原文及其例外条款。
- `provenance/imported-stock-assets.json`：导入封装与模型的来源、原库 ID、SHA-256 和文件头授权记录。
- `provenance/flori-migration.json`：当前库 ID 和路径与历史记录的对应关系。

以上路径均相对于本包的 `resources/<包标识>/` 安装目录。
STEP 文件保留原始字节和文件头声明。原始下载来源未记录的资源，仍按来源记录中的状态保留，
包元数据中的混合授权说明不代表为这些资源新增或变更授权。

导入封装仅调整资源引用，原有几何和模型变换参数保持。
