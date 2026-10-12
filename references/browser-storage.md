# 浏览器存储与文件处理依据

调研日期：2026-10-05。当前工具目录未提供 Context7，无法执行 resolve_library_id → query_docs；以下均为官方 MDN/Pillow 一手资料。本地旧视频模板仅能会话预览，因此新增持久化不沿用其假设。

| 依据 | 用于实现的结论 |
| --- | --- |
| [MDN IndexedDB](https://developer.mozilla.org/en-US/docs/Web/API/IndexedDB_API/Using_IndexedDB) | open/upgradeneeded 建立存储；readwrite 事务内同步入队 put；以 transaction.complete 判定保存成功，错误/中止保留当前编辑 |
| [MDN put](https://developer.mozilla.org/en-US/docs/Web/API/IDBObjectStore/put) | put 更新或插入并执行结构化克隆；草稿状态与上传 Blob 存在同一记录，避免先保存选择再丢失文件 |
| [MDN File API](https://developer.mozilla.org/en-US/docs/Web/API/File_API/Using_files_from_web_applications) | 用户选择或拖入 File，临时 object URL 用于解码；成功和失败都释放，长久保存不依赖 blob URL |
| [MDN readAsDataURL](https://developer.mozilla.org/en-US/docs/Web/API/FileReader/readAsDataURL) | 将上传原图转为可复制/导出的 data URL；落盘脚本解码并验证 |
| [MDN digest](https://developer.mozilla.org/en-US/docs/Web/API/SubtleCrypto/digest) | SHA-256 接收完整 ArrayBuffer；受安全上下文支持限制，不可用时拒绝未校验上传；单文件容量预算限制峰值内存 |
| [MDN 存储配额](https://developer.mozilla.org/en-US/docs/Web/API/Storage_API/Storage_quotas_and_eviction_criteria) | IndexedDB 受浏览器配额及清理影响；不能承诺永久保存，失败提示导出草稿 |
| [MDN localStorage](https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage) | file URL 的 localStorage 行为未规定，不能用它给本地 HTML 的长期恢复作保证；本实现也不将图片 Base64 塞入 localStorage |
| [Pillow Image](https://pillow.readthedocs.io/en/stable/reference/Image.html) | Image.open 获取格式/尺寸，load 实际解码；构建和交接核验原始字节，不变更图片 |
| [CSS Images 3：图像方向](https://drafts.csswg.org/css-images-3/#the-image-orientation)、[MDN naturalWidth](https://developer.mozilla.org/en-US/docs/Web/API/HTMLImageElement/naturalWidth) | 默认按 EXIF 定向；规范要求自然宽高按旋转后的图像计算，naturalWidth 代表自然尺寸，不能直接与未定向的编码宽度比较 |
| [Pillow EXIF](https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.Exif)、[exif_transpose](https://pillow.readthedocs.io/en/stable/reference/ImageOps.html#PIL.ImageOps.exif_transpose) | 本地 Pillow 11.3.0 的 exif_transpose 源码确认 Orientation 5/6/7/8 交换宽高；实现只读取 tag 274 并交换返回元信息，不执行转置或重编码 |

所有页面创建时间、访问人数/次数、点赞/评论数据均未知。MDN File API 最近修改时间可见为 2025-09-18；localStorage 为 2026-07-28；其余最近修改时间未采集。相关性基于实际使用的 API；权威性基于文档归属与原始接口说明，未用互动数据排序。

浏览器原生文件选择不提供可移植的原文件绝对路径。本实现仅把用户提供的原图字节与内容指纹交给本地脚本，脚本产生的路径才可进入发布交接。

没有启动浏览器时，只能报告脚本测试通过；IndexedDB 在实际本地 HTML/浏览器环境的恢复行为需由浏览器验收确认。存储不可用时保留会话编辑并提供草稿导出/导入，不声称已经持久化。
