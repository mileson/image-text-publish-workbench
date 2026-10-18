<a id="图文发布工作台"></a>

<div align="center">

# 图文发布工作台 · 发布前预览与选择

**把图片、标题和正文放到同一个本地页面里选好再交付。**

图片预览 · 文案编辑 · 候选选择 · 发布交接

[![中文说明](https://img.shields.io/badge/%E8%AF%B4%E6%98%8E-%E7%AE%80%E4%BD%93%E4%B8%AD%E6%96%87-059669)](#readme-detail-12)
[![项目类型](https://img.shields.io/badge/%E9%A1%B9%E7%9B%AE-Skill-6366f1)](#readme-detail-12)

[👀 效果预览](#readme-detail-12) · [✅ 适用场景](#readme-detail-14) · [🚀 第一次使用](#readme-detail-16) · [🧩 模块速查](#readme-detail-24) · [🤖 给 Agent 的任务示例](#readme-detail-18) · [📌 能做什么](#readme-detail-20)

</div>

---

[完整 Skill](SKILL.md) · MIT


图片在文件夹里，标题在聊天里，正文还有好几个版本。真正发布之前，你需要把它们放在一起，看清这次到底用哪张图、哪句话。这个工作台负责这一步。

<a id="readme-section-1"></a>

<a id="工作台效果"></a>

<a id="readme-detail-12"></a>

## 👀 效果预览

<table>
<tr>
<td width="50%" align="center"><a href="docs/screenshots/workbench-preview.png"><img src="docs/screenshots/workbench-preview.png" alt="淡白色遮盖对话与路径后的图文工作台效果示意" width="360"></a><br><sub>淡白色遮盖对话与路径后的图文工作台效果示意</sub></td>
<td width="50%" align="center"><a href="docs/screenshots/choose-title.png"><img src="docs/screenshots/choose-title.png" alt="标题候选与选中状态" width="360"></a><br><sub>标题候选与选中状态</sub></td>
</tr>
<tr>
<td width="50%" align="center"><a href="docs/screenshots/edit-body.png"><img src="docs/screenshots/edit-body.png" alt="正文版本与当前文案" width="360"></a><br><sub>正文版本与当前文案</sub></td>
<td width="50%" align="center"><a href="docs/screenshots/choose-tags.png"><img src="docs/screenshots/choose-tags.png" alt="图文发布包中的话题选择" width="360"></a><br><sub>图文发布包中的话题选择</sub></td>
</tr>
</table>

封面、图片顺序、标题和正文放在同一页里比较。选好之后，点击底部按钮，把当前发布信息复制给 AI 伙伴。

效果示意来自课件中的图文案例，左侧对话与本机路径已用淡白色遮盖，指令卡展示调用示例，不是实际执行回执。下面的局部截图保留实际演示界面，能看清具体选项。这组画面展示发布准备，不代表内容已在平台发布。

### 选标题


### 选正文、改文案


### 选话题


演示用的是中文内容。生成自己的工作台时，可以替换为自己的图片、标题和正文。

![从材料到发布准备的流程](docs/workflow.svg)

<a id="readme-section-2"></a>

<a id="适合哪些场景"></a>

<a id="readme-detail-14"></a>

## ✅ 适用场景

- 图文创作者：对比几张封面，调整内页顺序，再选标题和正文。
- 品牌或内容团队：把 AI 草稿交给同事复核，直接在同一个页面改。
- 教程、产品介绍、城市散步等题材：已有图片，想整理成一份可交接的发布材料。
- 使用 AI 伙伴的人：让 AI 先准备候选，自己最后选择，不必在聊天记录里翻找。

HTML 页面负责选择与编辑；打包的 Agent 流程可按需调研和生图，随后生成页面，不自动发布到社交平台。默认平台标识是 `xiaohongshu`；这是交接信息，不代表已经完成所有平台适配。

<a id="readme-section-3"></a>

<a id="第一次使用"></a>

<a id="readme-detail-16"></a>

## 🚀 第一次使用

这是一个可供 AI 读取的 Skill，也包含能直接运行的脚本。你不需要先配置社交平台账号。

1. 点击 GitHub 的 **Code → Download ZIP**，解压；或者克隆此仓库。
2. 使用 Python 3.10+。如果已有可用的 Python 环境，直接复用。在仓库目录安装依赖：

```bash
python3 -m pip install -r requirements.txt
```

3. 先跑全部使用合成图片的示例：

```bash
python3 examples/create_demo.py
```

4. 打开生成的 `output/demo.html`。点击标题、正文版本和话题，尝试上传自己的封面，再检查内页顺序。
5. 页面底部有 **复制发布信息给 AI**、**复制标题**、**复制正文与话题**。复制得到的是当前选择与编辑后的内容。

示例图片上写着 SYNTHETIC DEMO，只演示材料组织方式，不是实际拍摄作品。`output/` 默认不进入 Git。

### 让 AI 伙伴来准备

把整个仓库文件夹放进你的 Agent 支持的 Skill 目录。不同 Agent 的安装位置不同；以它的本地说明为准。也可以直接让能读取本地文件的 Agent 先读 `SKILL.md`。

> 请读取图文发布工作台 Skill。我已有这些图片和这份正文，帮我整理两个标题、两个正文版本，生成本地工作台。保留原文件，完成后我来选择，不发布。

把图片作为附件或提供存在的文件路径。AI 准备输入 JSON，然后运行校验与构建脚本；页面本身不连接模型，也不需要 API key。

### 使用自己的材料

复制 `examples/workbench-input.json`，按 [输入合同](references/input-contract.md) 修改。图片的 `path` 必须是你电脑上存在的绝对路径；没有图片时可以留空槽，在页面上传。标题和正文各至少一个候选。

```bash
python3 scripts/validate_workbench.py --input /absolute/path/input.json
python3 scripts/build_workbench.py --input /absolute/path/input.json --output /absolute/path/workbench.html
```

产物包括 HTML、规范输入 `.input.json` 和素材清单 `.assets.json`。HTML 内嵌图片预览，可在源图片移动后继续看图；要把图片交给后续任务时，仍会核验原路径和内容。

<a id="readme-section-4"></a>

<a id="告诉-ai-你想做什么"></a>

<a id="readme-detail-18"></a>

## 🤖 给 Agent 的任务示例

把完整仓库放进你的 AI 助手支持的 Skill 目录。支持斜杠调用的助手可以使用下面的指令；其他助手可以直接让它读取仓库里的 `SKILL.md`。斜杠形式取决于所用助手，不是网页里的按钮。

```text
/image-text-publish-workbench
准备一篇关于桌面整理的图文，面向第一次接触这个主题的人。
先调研，准备标题、正文和话题；需要图片时生成图片和封面。
有参考图册就参考构图与配色，不沿用旧主题和旧文案。
最后生成工作台，让我选择和修改。不要发布。
```

把“桌面整理”换成你的主题即可。产品介绍、教程、旅行笔记、知识卡片都可以，图片内容和数量按任务确定。

| 选项 | 你可以怎么说 |
|---|---|
| 调研 | “先调研”或“只用我的材料，不调研” |
| 图片准备 | “帮我生图”或“复用这些图片” |
| 图册参考 | “参考这份图册的构图与配色”或“不用参考图册” |
| 全流程 | “从主题开始，调研、准备图片和文案，再生成工作台” |

调研、生图的执行流程和提示词已经打包在本仓库的 [capabilities](capabilities/research/SKILL.md) 中，图片整理工具也随仓库分发。使用时需要你的 AI 助手有可用的浏览器或搜索、生图工具；没有这些工具仍可使用已有材料生成工作台。不会内置账号或密钥，也不会仅凭一句指令绕过付费、登录和授权。

能力来源与集成范围见 [说明](docs/capability-origins.md)。

[前置准备示例](examples/preparation-brief.json)给 Agent 读取；最终工作台仍使用原来的输入格式。

<a id="readme-section-5"></a>

<a id="能做什么"></a>

<a id="readme-detail-20"></a>

## 📌 能做什么

### 前置准备能力

- 按用户主题调研同类内容与事实，记录来源、可见互动数据和缺口。
- 复用用户图片，或调用可用生图工具制作当前主题的图片与封面。
- 可选参考用户图册的构图、配色和版式，保留原图，生成新副本。
- 根据实际材料生成标题、正文和话题候选，再输出可编辑工作台。

**可以完全自动准备吗？** 在你的 AI 助手具备相应工具、素材授权和必要预算时，可以用一次请求串起准备流程。登录、工具不可用或事实缺失时会报告缺口；静态页面不会自己调用模型。


![工作台区域及选择关系示意](docs/workbench-map.svg)

| 能力 | 你可以做什么 | 具体边界 |
|---|---|---|
| 封面比较 | 前置封面缩略图，点击选中 | 少于三张补上传空槽；多于三张按输入展示 |
| 内页整理 | 增加、移除、替换及调整内页顺序 | 不覆盖原始图片；封面始终是交接首图 |
| 标题候选 | 直接编辑并选择标题 | 与正文独立，不强制五套 |
| 正文版本 | 独立编辑和切换各版本 | 切换不会把别的版本覆盖 |
| 话题选择 | 查看、选择或取消话题 | 不承诺热度；来源未知保留未知 |
| 图片上传 | 点击或拖入 JPEG、PNG、WebP | 实际解码、尺寸、大小及内容指纹校验；仅静态图片 |
| 草稿恢复 | 当前浏览器后台保存编辑和上传原图 | 依赖浏览器存储；清理数据、换地址或换浏览器可能影响恢复 |
| 内容检查 | 提醒标题、正文与话题数量超限 | 默认 16/1000/10 是工作台配置，不是平台实时官方限制 |
| 当前稿复制 | 复制当前标题、正文、话题和所选图片信息 | 缺封面或有未恢复图片时阻断完整交接；失败可手动复制 |
| 素材落盘 | 把页面上传的原图变成可核验的本地文件 | 先验证全部图片，再写入指定目录；不上传网络 |
| 单文件预览 | 在本地打开 HTML 评审 | 图片内嵌；编辑不会自动写回原 HTML |

默认资源预算：单图 32 MiB、整组 200 MiB、每张不超过 3600 万像素。预览保留比例，不自动裁图。EXIF 方向会用于展示尺寸；原始图片字节和元数据不会因落盘而改变。

<a id="readme-section-6"></a>

<a id="把选好的材料交给下一步"></a>

<a id="readme-detail-22"></a>

## 📤 交付选好的材料

页面复制的发布信息含当前稿和图片。浏览器上传图片没有天然本地路径，因此不能凭文件名猜测它在哪个文件夹。

把复制内容保存为文本，或把页面接口返回的选择对象保存为 JSON，再运行：

```bash
python3 scripts/materialize_selection.py --selection /absolute/path/publish-selection.json --output-dir /absolute/path/current-assets
```

脚本会输出 `publish-selection.resolved.json` 并落盘上传原图。实际发布需要另外获得授权的任务接手。开发者可读取：

```javascript
await window.workbenchReady;
const selection = await window.getPublishReviewSelection();
const draft = await window.getWorkbenchDraft();
```

<a id="readme-section-7"></a>

<a id="仓库导航"></a>

<a id="readme-detail-24"></a>

## 🧩 模块速查

按要处理的工作选择入口，先看模块职责，再进入对应文件或目录。

| 模块入口 | 负责什么 | 什么时候看 |
| --- | --- | --- |
| [`SKILL.md`](SKILL.md) | Agent 使用规则与执行入口 | 让 Agent 读取任务规则、所需材料与交付要求 |
| [`assets/`](assets/) | 项目图片与静态素材 | 维护图片、静态文件和展示素材 |
| [`capabilities/`](capabilities/) | 可独立阅读的能力模块 | 查找具体场景对应的技能入口 |
| [`docs/`](docs/) | 项目说明与参考文档 | 查阅运行、设计与维护约定 |
| [`examples/`](examples/) | 可参考的输入与调用示例 | 用现有样例核对输入格式和调用方式 |
| [`references/`](references/) | 技能规则与输入输出合同 | 核对输入约定、操作细节与适用边界 |
| [`scripts/`](scripts/) | 开发与维护脚本 | 查找构建、验证或维护的现有命令 |

<a id="readme-section-8"></a>

<a id="常见问题"></a>

<a id="readme-detail-26"></a>

## ❓ 常见问题

**没有图片还能用吗？** 可以先生成空槽，再上传；完整发布交接需要选好可用封面。

**只有一套标题和正文可以吗？** 可以，至少各一套即可，不必凑满五套。

**打开 HTML 就会自动调用 AI 吗？** 不会。AI 在上游准备材料，页面负责评审与整理。

**会替我发布吗？** 不会，也不需要社交平台登录。复制信息后再交给你授权的发布流程。

**为什么刷新后没恢复？** 浏览器存储可能被禁用或清理，文件地址也可能变了。保留当前稿备份，不把浏览器自动保存当唯一备份。

**为什么复制按钮被拦截？** 本地页面可能没有剪贴板权限；页面提供手动复制方式。检查最终复制内容后再使用。

**图片上传会覆盖原文件吗？** 不会；替换发生在页面草稿中，落盘写到你指定的输出目录。

**能给其他人发生成的 HTML 吗？** 可以，但它包含原图预览和素材路径；先自行脱敏。不应把含隐私的生成文件提交到公开仓库。

**会自动去掉照片的位置和 EXIF 吗？** 不会，上传原图与落盘保留字节。公开分享前单独检查和处理图片元数据。

**支持其他平台吗？** 输入可设置平台标识和容量；它不自动适配所有平台，也不核验实时发布规则。

<a id="readme-section-9"></a>

<a id="验证与开发"></a>

<a id="readme-detail-28"></a>

## 🧪 验证与开发

修改后使用项目已有的检查入口核对结果，命令与检查范围如下。

```bash
python3 scripts/test_workbench.py
```

回归覆盖构建、编辑状态、图片指纹与素材交接。自动脚本不等于浏览器视觉验收。发布检查见 [验证记录](docs/verification.md)。完整使用约定见 [SKILL.md](SKILL.md) 和 [输入合同](references/input-contract.md)。

<a id="readme-section-10"></a>

<a id="隐私与许可证"></a>

<a id="readme-detail-30"></a>

## 📄 隐私与许可证

此公开副本清除了私人执行记录、特定作者的封面与品牌推广偏好。示例仅使用合成图和通用文案。生成文件可能包含你输入的正文、图片、路径和元数据，默认保存在 Git 忽略的目录。

代码和原创文档采用 [MIT](LICENSE)。你提供的照片、字体、品牌和第三方素材仍遵守各自权利，不因工作台导出而转为 MIT。
