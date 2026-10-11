---
version: 1.0.0
name: Qwen-Image-Turbo-SDCPP-System
description: A warm-editorial local generative image service and OpenAI-compatible Agent API gateway, powered by stable-diffusion.cpp and Qwen-Image-2.1-Turbo (Uncensored). Features physical OS-level VRAM lifecycle management (Always-On, On-Demand Cold Start, and Auto-Unload TTL), single-task GPU serialized queueing, and a Claude-inspired warm cream/coral visual interface.

colors:
  primary: "#cc785c"
  primary-active: "#a9583e"
  primary-disabled: "#e6dfd8"
  ink: "#141413"
  body: "#3d3d3a"
  body-strong: "#252523"
  muted: "#6c6a64"
  muted-soft: "#8e8b82"
  hairline: "#e6dfd8"
  hairline-soft: "#ebe6df"
  canvas: "#faf9f5"
  surface-soft: "#f5f0e8"
  surface-card: "#efe9de"
  surface-cream-strong: "#e8e0d2"
  surface-dark: "#181715"
  surface-dark-elevated: "#252320"
  surface-dark-soft: "#1f1e1b"
  on-primary: "#ffffff"
  on-dark: "#faf9f5"
  on-dark-soft: "#a09d96"
  accent-teal: "#5db8a6"
  accent-amber: "#e8a55a"
  success: "#5db872"
  warning: "#d4a017"
  error: "#c64545"

typography:
  display-lg:
    fontFamily: "Copernicus, Tiempos Headline, Georgia, serif"
    fontSize: 40px
    fontWeight: 400
    lineHeight: 1.15
    letterSpacing: -1px
  display-md:
    fontFamily: "Copernicus, Tiempos Headline, Georgia, serif"
    fontSize: 28px
    fontWeight: 400
    lineHeight: 1.2
    letterSpacing: -0.5px
  title-lg:
    fontFamily: "StyreneB, Inter, system-ui, sans-serif"
    fontSize: 20px
    fontWeight: 500
    lineHeight: 1.3
    letterSpacing: 0
  title-md:
    fontFamily: "StyreneB, Inter, system-ui, sans-serif"
    fontSize: 16px
    fontWeight: 500
    lineHeight: 1.4
    letterSpacing: 0
  body-md:
    fontFamily: "StyreneB, Inter, system-ui, sans-serif"
    fontSize: 15px
    fontWeight: 400
    lineHeight: 1.55
    letterSpacing: 0
  body-sm:
    fontFamily: "StyreneB, Inter, system-ui, sans-serif"
    fontSize: 13px
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: 0
  caption:
    fontFamily: "StyreneB, Inter, system-ui, sans-serif"
    fontSize: 12px
    fontWeight: 500
    lineHeight: 1.4
    letterSpacing: 0.5px
  code:
    fontFamily: "JetBrains Mono, ui-monospace, monospace"
    fontSize: 13px
    fontWeight: 400
    lineHeight: 1.55
    letterSpacing: 0
  button:
    fontFamily: "StyreneB, Inter, system-ui, sans-serif"
    fontSize: 14px
    fontWeight: 500
    lineHeight: 1
    letterSpacing: 0

rounded:
  sm: 6px
  md: 8px
  lg: 12px
  xl: 16px
  pill: 9999px

spacing:
  xs: 8px
  sm: 12px
  md: 16px
  lg: 24px
  xl: 32px
  section: 64px

components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.button}"
    rounded: "{rounded.md}"
    padding: 10px 20px
    height: 40px
  button-secondary:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    border: "1px solid {colors.hairline}"
    typography: "{typography.button}"
    rounded: "{rounded.md}"
    padding: 10px 18px
    height: 40px
  button-flush-vram:
    backgroundColor: "{colors.surface-soft}"
    textColor: "{colors.error}"
    border: "1px solid {colors.hairline}"
    typography: "{typography.button}"
    rounded: "{rounded.md}"
    height: 36px
  status-badge-resident:
    backgroundColor: "{colors.surface-card}"
    textColor: "{colors.success}"
    typography: "{typography.caption}"
    rounded: "{rounded.pill}"
    padding: 4px 10px
  status-badge-cold:
    backgroundColor: "{colors.surface-soft}"
    textColor: "{colors.muted}"
    typography: "{typography.caption}"
    rounded: "{rounded.pill}"
    padding: 4px 10px
  card-feature:
    backgroundColor: "{colors.surface-card}"
    textColor: "{colors.ink}"
    rounded: "{rounded.lg}"
    padding: 24px
  card-product-dark:
    backgroundColor: "{colors.surface-dark}"
    textColor: "{colors.on-dark}"
    rounded: "{rounded.lg}"
    padding: 24px
  input-text:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    border: "1px solid {colors.hairline}"
    rounded: "{rounded.md}"
    padding: 10px 14px
---

# Qwen-Image-2.1-Turbo 本地可视化与 Agent API 策划与设计规范 (DESIGN.md)

## 1. 概述 (Overview)

本方案旨在为个人工作站及局域网环境构建一套高效率、低摩擦、无审查的本地生图系统。系统依托 `stable-diffusion.cpp` 高性能 GGUF 推理核心，加载 `Qwen-Image-2.1-Turbo` 与 `Qwen3-VL-8B` Abliterated（无审查）文本编码器，向外同时提供**符合 Claude 人文风骨的 Web 可视化工作台**与**高度兼容 OpenAI DALL-E 规范的 Agent REST API**。

整体设计语言参照 Claude 的 **Warm Editorial（暖色调出版物）** 风格：以暖米色（Cream Canvas `#faf9f5`）作为底层基调，以暖珊瑚色（Coral `#cc785c`）作为主视觉触发与操作纽带，以暗炭黑（Surface Dark `#181715`）作为代码、终端及 API 观察视窗。

### 核心价值主张
1. **显存治理自由**：支持「显存常驻（秒级出图）」与「冷启动即用即走（零闲置显存）」双策略自由切换，并提供超时智能休眠。
2. **Agent 无缝兼容**：任何支持 OpenAI `/v1/images/generations` 的外部智能体（Dify、FastGPT、Chatbox、Cherry Studio 等）零代码改造直接接入。
3. **极简代码实现**：严格遵循奥卡姆剃刀原则，全系统仅需 1 个主程序文件，摒弃臃肿的前端工程构建与脆弱的 C++ 动态链接绑定。

---

## 2. 架构拓扑与分析 (Architecture Analysis)

### 2.1 拓扑架构：Sidecar 进程隔离型双层网关

```
                     [ 外部生态 / 客户端 ]
            ┌─────────────────┴─────────────────┐
            ▼                                   ▼
   [ Web 浏览器用户 ]                   [ Agent / 第三方工具 ]
   (Claude Warm UI)              (Dify, Cherry Studio, Chatbox)
            │                                   │
            │ HTTP: 40188                        │ POST /v1/images/generations
            └─────────────────┬─────────────────┘
                              ▼
┌───────────────────────────────────────────────────────────────┐
│  业务网关与调度核心 (Python: FastAPI + Gradio)                 │
│                                                               │
│  · 协议层: OpenAI DALL-E 规范兼容、CORS 跨域、多余入参宽容解析 │
│  · 参数固化层: 注入 Turbo Sigmas、Steps=8、CFG=1.0、FlashAttn │
│  · 任务排队锁: asyncio.Lock() GPU 任务强制串行，防止显存 OOM   │
│  · 资产服务: outputs/ 静态映射与 Base64 双通道分发            │
│  · 显存管理器 (VRAM Lifecycle Controller): 进程级拉起/终止    │
└───────────────┬───────────────────────────────┬───────────────┘
                │                               │
       [策略: 冷启动 (On-Demand)]      [策略: 显存常驻 (Always-On)]
                │                               │
                ▼ 子进程 run (完成后立即退出)     ▼ 守护进程 Popen (HTTP: 40189)
┌───────────────────────────────┐       ┌───────────────────────────────┐
│   sd-cli.exe                  │       │   sd-server.exe               │
│   (单次运行，显存物理清空)     │       │   (模型常驻 VRAM，秒级推理)   │
└───────────────────────────────┘       └───────────────────────────────┘
                ▲                               ▲
                └───────────[ GPU 显存 ]────────┘
```

### 2.2 为什么采用这种架构？（深度对比）

1. **操作系统级物理显存回收 vs 框架内软卸载**
   * *问题*：直接在 Python 进程中通过 C-binding 或 PyTorch 卸载 15GB 模型，常因 CUDA 缓存、内存池残留或对象循环引用导致“假释放”。
   * *解法*：Sidecar 架构将推理过程隔离在独立 OS 进程中（`sd-cli.exe` 或 `sd-server.exe`）。当需要释放显存时，**直接杀掉子进程，显卡驱动与操作系统瞬间 100% 物理级回收全部显存**，绝不残留。
2. **故障隔离（Fault Isolation）**
   * 底层 C++ 推理引擎若因异常 Prompt 或显存溢出发生 Segfault/Crash，主网关进程毫发无损。网关可记录错误日志并优雅通知用户或 Agent，而不会造成服务整体瘫痪。
3. **免编译跨版本维护（Zero-Compilation）**
   * 无需在 Windows 平台配置复杂的 CMake、MSVC 与 CUDA 编译环境，直接调用社区官方发布的预编译二进制文件。

---

## 3. 显存策略机制 (VRAM Lifecycle Policy)

系统在控制台和 Web UI 提供三档策略开关：

| 策略模式 | 底层运行行为 | 显存表现 | 出图响应延迟 | 适用工作场景 |
| :--- | :--- | :--- | :--- | :--- |
| **显存常驻 (Always-On)** | 启动后台常驻 `sd-server.exe` 进程，模型保持在显存。 | 持续占用 12~15GB | **极速**：2~4 秒 | 批量产图、高频人机交互、连续调试。 |
| **按需冷启动 (On-Demand)** | 收到请求才通过 `sd-cli.exe` 运行，生成完成后进程自动结束。 | 闲置占用 0MB；生图时临时占用 | **较慢**：需读盘 15~20 秒 + 推理 3 秒 | 偶发生图、显存极其紧缺、需与游戏或本地大模型交替使用。 |
| **智能休眠 (Auto-Unload)** *(默认推荐)* | 首个请求拉起常驻服务；若连续 $N$ 分钟（默认 5 分钟）无请求，后台自动终止子进程。 | 忙时常驻，闲时 0MB | 忙时 2~4 秒；唤醒首张需冷启动 | 日常混合开发、个人工作站与轻量 Agent 后台。 |

*注：界面提供独立的「立即释放显存 (Flush VRAM)」按钮，任何时候点击均可一键强杀常驻进程，显存归零。*

---

## 4. 视觉界面设计规范 (UI & Editorial Guidelines)

整体设计严格遵循 Claude 设计语言规范：

### 4.1 页面色彩节奏 (Color & Surface Rhythm)
* **底色 (Canvas)**：暖米色 `#faf9f5`，杜绝冷冰冰的纯白或灰白。
* **卡片 (Surface Card)**：比底色稍深的温暖米灰 `#efe9de`，承载参数选择器与历史画廊。
* **暗色产品视窗 (Surface Dark)**：深炭黑 `#181715`，用于展示图片生成日志、系统状态与 Agent API 交互代码示例。
* **主按键 (Primary CTA)**：暖珊瑚色 `#cc785c`，圆角 8px，悬浮加深至 `#a9583e`。

### 4.2 字体排印 (Typography)
* **主标题**：Serif 衬线字体（优先 `Copernicus` / `Tiempos Headline` / `Georgia`），字重 400，负字间距。
* **正文与标签**：Humanist 无衬线字体（优先 `StyreneB` / `Inter` / 系统默认无衬线）。
* **代码与终端**：等宽字体（`JetBrains Mono` / `ui-monospace`）。

### 4.3 界面布局结构 (Layout)
* **顶部导航 (Top Nav)**：高度 60px，承载品牌标识、当前显存策略指示 Badge（绿色常驻 / 灰色休眠）、一键释放显存按钮。
* **左右分栏工作区**：
  * **左侧控制面板**：Prompt 多行输入框、预设分辨率快速切换 Pills（1024x1024, 768x1024 等）、随机种子控制器、显存策略选择器。
  * **右侧主画布**：大图预览区、生成用时统计、保存/复制按钮。
* **下方暗色视窗 (Dark Code Card)**：提供当前生成的 cURL 命令与 Agent 接入代码预览，方便直接复制给第三方工具使用。

---

## 5. 手动下载与部署清单 (Manual Download Checklist)

> **重要提示**：本系统**不会自动下载任何模型与二进制执行文件**。请严格按照以下说明**手动下载**并放置在指定目录下。

### 5.1 目录结构规划
在 `e:\image2\` 下建立如下层级（各模块分门别类，便于多模型管理与后续扫描切换）：

```text
e:\image2\
├── bin\                     # 存放 stable-diffusion.cpp 预编译可执行文件与 dll
├── models\                  # 模型根目录
│   ├── diffusion\           # 降噪主模型 (DiT / Denoiser GGUF)
│   ├── text_encoder\        # 文本编码器 (LLM / Qwen3-VL GGUF)
│   └── vae\                 # 变分自编码器 (VAE safetensors)
├── outputs\                 # 自动生成，存放生成后的图片与静态映射
├── app.py                   # 核心服务代码（API + UI + 调度）
└── requirements.txt         # Python 依赖
```

### 5.2 需要手动下载的文件列表

#### 1. 推理引擎：`stable-diffusion.cpp` Windows 预编译包
* **下载页面**：[GitHub - leejet/stable-diffusion.cpp Releases](https://github.com/leejet/stable-diffusion.cpp/releases)
* **下载文件**：选择最新的支持 CUDA 的压缩包，例如 `sd-master-XXXXX-bin-win-cuda-cu12.X-x64.zip`。
* **放置路径**：解压其中的 `sd-cli.exe`、`sd-server.exe` 以及配套的 `.dll` 文件至：
  `e:\image2\bin\`

#### 2. 文本编码器：Qwen-Image-2.1-Turbo Abliterated Uncensored (GGUF)
* **仓库地址**：[AtomicChat/Qwen-Image-2.1-Turbo-Uncensored-GGUF](https://huggingface.co/AtomicChat/Qwen-Image-2.1-Turbo-Uncensored-GGUF)
* **推荐版本**（二选一）：
  * **Q8_0（画质首选，8.71 GB）**：`Qwen-Image-2.1-Turbo-Abliterated-Uncensored-Q8_0.gguf`
  * **AD-Q4_K（平衡首选，5.29 GB）**：`Qwen-Image-2.1-Turbo-Abliterated-Uncensored-AD-Q4_K.gguf`
* **放置路径**：
  `e:\image2\models\text_encoder\`

#### 3. 降噪主模型：Qwen-Image-2.1-Turbo Denoiser (GGUF)
* **仓库地址**：[AtomicChat/Qwen-Image-2.1-Turbo-GGUF](https://huggingface.co/AtomicChat/Qwen-Image-2.1-Turbo-GGUF)
* **推荐版本**：`Qwen-Image-2.1-Turbo-AD-Q4_K.gguf` 或 `Q8_0.gguf`
* **放置路径**：
  `e:\image2\models\diffusion\`

#### 4. VAE 模型：Qwen-Image-2.1 VAE (Safetensors)
* **仓库地址**：[Comfy-Org/Qwen-Image-2.1](https://huggingface.co/Comfy-Org/Qwen-Image-2.1/tree/main/split_files/vae)
* **下载文件**：`qwen_image_2.1_vae_bf16.safetensors`
* **放置路径**：
  `e:\image2\models\vae\`


---

## 6. 第三方 Agent 接口规范 (API Specification)

系统对外暴露与 OpenAI DALL-E 100% 兼容的接口。

* **Endpoint**: `POST http://127.0.0.1:40188/v1/images/generations`
* **Headers**: `Content-Type: application/json`

### 6.1 请求示例 (Request)
```json
{
  "prompt": "a cinematic portrait of an astronaut in a lush jungle, 8k, warm sunlight",
  "size": "1024x1024",
  "n": 1,
  "response_format": "url"
}
```

### 6.2 响应示例 (Response)
系统始终同时附带静态访问 `url` 与 Base64 编码 `b64_json`，彻底通杀所有第三方工具：
```json
{
  "created": 1728619200,
  "data": [
    {
      "url": "http://127.0.0.1:40188/outputs/img_1728619200_42.png",
      "b64_json": "iVBORw0KGgoAAAANSUhEUgAABAAAAAQACA..."
    }
  ]
}
```

---

## 7. 实施准则 (Do's and Don'ts)

### Do
* 优先使用操作系统级进程边界管理显存，释放必须依赖终止进程。
* 始终保持 Turbo 模型的超参锁定：`steps=8`, `cfg=1.0`, `sampling_method=euler`, 以及特定 sigmas 序列。
* 保持界面冷暖节奏对比：暖米色背景为主，暗色视窗仅用于承载技术细节。
* 保持 API 容错性：忽略客户端传入的未定义字段（如 `quality`, `style`），避免返回 422 错误。

### Don't
* 不要在 Python 内部尝试使用 ctypes/C-bindings 强行常驻同一进程，增加崩溃与排查成本。
* 不要在没有队列锁（Lock）的情况下允许并发推理，必须强制排队防止 GPU OOM。
* 不要在自动化脚本中隐式下载数 GB 的模型权重，必须明确交由用户手动管理。
