# PCM 打包与发布

此流程生成 KiCad 10 PCM v2 包。日常编辑继续使用 Git 工作副本，分发设备使用安装包。
自动化版本采用日历格式，不需要手动维护语义版本或创建标签。
本机包内容与隔离配置验证结果见[本地验证记录](pcm-validation-2026-11-04.md)。

## 自动化入口

| 操作 | 结果 |
| --- | --- |
| 库或打包相关变更推送到 `main`（包括合并 PR） | 自动打包、上传附件、发布 Release，并更新 PCM 订阅入口 |
| 库或打包相关变更推送到其他分支 | 自动生成 `development` 安装包制品，不发布 Release |
| 仅修改普通维护文档后推送 | 只执行清单逻辑检查和差异检测，不打包、不发布 |
| PR 创建、更新或重新打开 | 自动生成合并结果的安装包制品，不发布 Release |
| Actions → PCM 打包与发布 → Run workflow | 自动生成版本，可选择状态；默认仅生成制品，仅 `main` 可以勾选发布 |

打包输入的唯一清单是 [tools/pcm-inputs.json](../tools/pcm-inputs.json)。
构建器和 CI 都通过 `tools/pcm_manifest.py` 读取它，工作流中不再维护 `push.paths`。
普通文档也会启动轻量 `changes` 任务，完成检查后跳过 `package` 和 `release`；
PR 和手动触发保留打包，不受差异检测结果影响。

清单包含以下内容：

- `metadata`：包元数据源文件；自动参与触发判定。
- `files`：直接打包的文件或 glob、可选扩展名过滤、包内目标路径及 JSON 字段移除规则。
  文件收集和变更判定共用这些规则，因此新增包输入只需在此增加条目。
- `build_inputs`：不放进安装包、但会影响构建结果的辅助代码和配置。
  已列在 `files` 中的文件无需重复登记。清单自身也自动参与触发判定。

glob 中的 `*` 不跨目录，`**` 匹配零级或多级目录；扩展名过滤不区分大小写。
固定源文件缺失、路径越界或包内目标冲突会使构建失败。
安装包直接收集当前主库，不生成历史兼容库、别名或路径配置工具。

推送比较完整的 `before` → `after` Git 差异，覆盖一次推送内的全部提交；
重命名拆为旧路径删除与新路径增加，删除的文件也能触发。
使用 checkout 的完整历史与本地 Git，不依赖 GitHub 路径过滤的文件数量限制。
新分支、缺失比较基线或强制推送导致旧提交不可读时，保守执行打包，避免漏发。
清单格式错误会使检查失败，不作为“没有包变更”处理。

需要本地预览是否命中时，可执行以下只读命令：

```powershell
python -B tools/pcm_manifest.py --base HEAD~1 --head HEAD
```

需要验证打包但暂不发布时，在此次推送最后一个提交的说明中加入 `[skip release]`。
该标记只跳过这次推送的 Release，保留打包和下载制品；手动触发的发布不受影响。
不需要为说明文字或排版的小修补创建新版本，修改随下次正常发布带出。

主分支制品保留 30 天，可在 Actions 对应运行的 Artifacts 中下载。
解压下载制品的外层 ZIP，才能取得真正的 `Flori-KiCad-Library-<版本>.zip`。
普通分支和 PR 制品用于安装验证；PR 制品对应 GitHub 生成的合并提交。
同一提交重新运行工作流时，下载名称中的运行 ID 和尝试次数可用于区分。

版本格式为 `YYYY.MMDD.N`，例如 `2026.1104.123`：上海时区的年、月日及本工作流的累计运行编号。
月份与日期保留两位，例如 `2026.0105.124`。编号不按天重置，允许因 PR、分支构建或失败运行而跳号。
Release 标题直接使用该版本，自动生成的 Git 标签为 `v2026.1104.123`；无需手动创建或推送标签。
提交 SHA 放在发布说明中，不拼进名称。包名为 `Flori-KiCad-Library-2026.1104.123.zip`。
重新运行当天的同一次工作流沿用版本，不覆盖已经发布的 Release；跨天重新运行可能产生新的日期版本。

日常只需正常提交并推送到主分支，或合并 PR：

```powershell
git push origin main
```

首次也可手动触发，保持 `publish` 未勾选，先按[安装与检查说明](../pcm/INSTALL_zh.md)验证。
主分支自动发布时 PCM 状态为 `stable`，表示进入日常订阅通道，不代表 CI 已执行完整的 KiCad 图形界面检查。
工作流使用实际 `GITHUB_REPOSITORY` 生成链接；以后上游改名无需调整工作流。
本流程不负责仓库改名、提交或推送本地修改。

自动流程运行在 GitHub 托管的 Ubuntu runner 上：Python 负责打包，Actions 负责保存制品，
最后通过 runner 预装的 `gh release create` 创建 Release 并上传附件。
发布认证使用 GitHub 自动提供的 `${{ github.token }}`，通过 `GH_TOKEN` 传入，
不依赖开发机的 `gh` 安装或登录状态，也不需要单独配置个人访问令牌。
开发机只需正常使用 Git 推送；本地独立打包只需要 Python。

## 本地命令（需要时自行执行）

Python 3.10 以上，无需安装第三方依赖。在仓库根目录执行：

```powershell
python tools/build_pcm.py --version 2026.1104.123 --status testing
```

输出位于 `dist/pcm/2026.1104.123/`，该目录已加入 Git 忽略规则：

- `Flori-KiCad-Library-2026.1104.123.zip`：PCM 安装包，根目录包含 `metadata.json`。
- 同名 `.sha256`：安装包摘要；`.metadata.json`：外部元数据，包含下载信息与版本历史。
- `packages.json`：PCM 包目录；`repository.json`：自定义 PCM 仓库入口。
- `release-notes.md`：中文发布说明草稿。

输出不覆盖已有文件。需要重打时，使用新的 `--output-dir <目录>`。
可用 `--repository owner/repository` 调整下载地址；默认使用元数据主页中的当前仓库名。
下载地址只有在同名 Release 及附件实际上传后才有效；Actions 普通制品只用于“从文件安装”。

发布后续版本时用 `--previous-packages <上一版 packages.json>` 合并历史。
也可用 `--previous-packages-url <HTTPS URL>`；仅 404 视为首版，其余网络错误直接失败。
自动发布读取最新稳定 Release 的公开 `packages.json`，因此当前在线订阅方案要求仓库和附件公开可访问。
正式版本应递增，已存在的版本或 Release 不覆盖。
预发布只继承最新稳定版的历史，不累积其他预发布；需要完整预发布历史时手动传入上一版索引。
发布流程从读取历史索引到上传附件共用并发锁，排队等待，不因后一次推送主动取消前一次待执行任务。
GitHub 排队上限为 100；失败运行需在 Actions 查看日志后重试，自动化不会替你修复库文件错误。

## 本机源码与 PCM 安装的冲突处理

同一个 KiCad 配置中，每个 `PCM_Flori_*` 昵称只保留一个来源。
已经由源码脚本注册的同名条目，会与 PCM 自动注册目标重叠；不能把“包已经解压”当作库表已正确切换。

建议开发机保留日常源码配置，用独立配置测试 PCM：

1. 关闭测试用 KiCad，在临时目录准备独立的配置根目录、用户资料目录和 PCM 安装目录。
2. 仅对测试进程设置 `KICAD_CONFIG_HOME`、`KICAD_DOCUMENTS_HOME` 和 `KICAD10_3RD_PARTY`。
3. 在该测试环境初始化标准库，通过 PCM 从文件安装。
4. 关闭测试进程后，从正常入口打开 KiCad，即继续使用日常源码库。

不需要删除官方库、源码工作副本或日常配置。避免把上述测试变量写成系统环境变量。
若确定要把日常配置切换成 PCM，先备份库表，仅移除指向源码的 Flori 主库和旧别名注册项，
再通过 PCM 安装；原始库文件应继续保留，便于恢复和维护。

## 包内容和路径

包标识固定为 `com.github.flowersauce.flori-kicad-library`，与本地目录和上游仓库名独立。
安装后的目录标识为 `com_github_flowersauce_flori-kicad-library`。
主库仍注册为 `PCM_Flori_*`，请保留默认 `PCM_` 前缀并启用自动添加库表。

构建器仅收集主库、STEP/STP/WRL 模型、PDF/DWG 资料及必要的安装说明、来源记录和许可证。
保留已存储的未引用模型变体，不包含 `.git`、`tmp`、本机配置或旧库副本。

源码中的 `${FLORI_KICAD_DIR}` 在内存中的包内容里转换为
`${KICAD10_3RD_PARTY}/3dmodels/<目录标识>/` 或 `resources/<目录标识>/`。
官方 `${KICAD10_3DMODEL_DIR}` 和器件字段变量保留。
构建器会拒绝未转换的源码变量、缺失的包内引用和重复版本；不改写源码或当前设备配置。
ZIP 文件顺序、时间戳及权限固定，摘要按实际 ZIP 字节计算；索引更新时间使用打包时的 UTC 时间。

包只提供 4 个符号分类和 5 个封装分类，均使用 `PCM_Flori_*` 昵称。
不支持旧名称兼容，不需要安装后的 Python 配置步骤。
源码与 PCM 安装不能同时占用相同昵称；开发机继续直接使用源码配置脚本。
授权说明位于包的 `resources/licenses/`，原始来源与迁移映射位于 `resources/provenance/`。

## 在 PCM 中订阅更新

发布首个稳定 Release 后，可在 PCM 仓库管理中添加：

```text
https://github.com/flowersauce/Flori-KiCad-Library/releases/latest/download/repository.json
```

该入口跟随最新稳定版本，内含的 `packages.json` 摘要与同版附件配套。
仓库改名后使用新地址。测试发布的入口使用对应 Release 的固定下载地址，不推动稳定订阅更新。
仅创建 GitHub Release 不等于进入 KiCad 官方默认仓库；这里使用自定义仓库或“从文件安装”。

规范参考：[KiCad PCM 打包说明](https://dev-docs.kicad.org/en/addons/index.html)、
[GitHub Actions 排队与并发控制](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency)。
