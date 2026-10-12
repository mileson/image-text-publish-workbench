# 输入与交接合同

输入示例见 `../examples/workbench-input.json`；正式 JSON schema 见 `workbench-input.schema.json`。

| 字段 | 要求 |
| --- | --- |
| schema_version | `image-text-publish-workbench.input.v1` |
| document_id / topic | 非空稳定文档 ID / 主题；不同内容使用不同 ID |
| platform | 默认 `xiaohongshu`，作为交接元数据，不自动触发平台适配 |
| titles | 至少 1 个 `{id,label,text,note?}`；ID 唯一 |
| body_variants | 至少 1 个 `{id,label,text}`；与标题独立 |
| selected_title_id / selected_body_id | 默认各自首项 |
| tags | `{name,selected,reason,source_url?}`；不要把 `#` 放入 name，来源未知用 null |
| covers / photos | `{id,label,path,role}`；path 为存在的绝对路径，role 对应 cover/photo；图片 ID 全局唯一，不以 `upload-` 起始 |
| selected_cover_id | 默认首张封面，无封面时 null |
| limits | 可覆盖 title/body/tags/max_upload_bytes；默认 16/1000/10/33554432 |

图片格式为 JPEG、PNG、WebP，原图不裁切；单张默认 32 MiB，单组 200 MiB，3600 万像素是工作台资源预算。输入图片必须静态。预览保持原比例；3:4 是常见输入，不是强制尺寸。

`width` / `height` 采用 EXIF 方向校正后的展示尺寸，与浏览器图片预览的自然尺寸对齐。Orientation 5/6/7/8 交换原始编码宽高；仅修正元信息，源图片和导出落盘字节、EXIF、SHA-256 均保持原样。

校验器会检查候选 ID、默认选择、文件存在、实际解码、大小、SHA-256（若输入提供）及默认文案容量。正文容量包含尾部话题，正文与话题之间恰好一个空白行。计数为 Unicode 码点，不宣称等同所有平台的官方计数。

构建产出：HTML（全部预览内嵌）、同名前缀 `.input.json`（去掉 Base64 的规范输入）、`.assets.json`（原文件元信息）。HTML 中原图仍可在源文件被移动后预览，但交接时必须重新核验原路径。浏览器编辑不会写回 HTML 或输入 JSON。

发布信息版本为 `image-text-publish-workbench.selection.v1`：包含当前 title/body/tags/composed_body、当前封面 `cover`、按发布顺序排列的 `images`、limits、有效性标志与 `review_only:true`。`images[0]` 必须是 cover，其余为 photo。每张图片含 id/fileName/size/sha256/width/height/mime/role/source/path/publishable。来源 `registered` 有真实 path；来源 `uploaded` 的 path 固定 null，随复制和导出携带 data_url，落盘脚本验证后才变为 registered。

草稿版本为 `image-text-publish-workbench.draft.v1`：document_id、输入指纹、编辑状态与使用中的上传图片。只允许导入同一文档与输入指纹的草稿，避免另一份内容覆盖当前文案；更新输入会建立新草稿空间，旧草稿不被迁移改写。

本 Skill 不负责实时平台规则调查、图片生成或自动发布。需要新平台时先确认目标发布要求，再通过 limits 和上游文案处理适配。
