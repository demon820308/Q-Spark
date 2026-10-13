<div align="center">
  <img src="assets/logo.png" alt="Q-Spark" width="100" />
  <h1>Q-Spark 生图控制台</h1>
  <p><strong>基于 stable-diffusion.cpp C++ 原生引擎的轻量高性能本地 AI 生图工作室，支持兼容 OpenAI 的 Agent API。</strong></p>
  <p>
    <a href="https://github.com/demon820308/Q-Spark/releases/latest">下载便携版 v0.2.5</a> ·
    <a href="#核心功能特性">核心特性</a> ·
    <a href="#快速上手">快速上手</a> ·
    <a href="#模型库与目录规范">模型库指引</a> ·
    <a href="#agent-api-接口">Agent API</a> ·
    <a href="README.md">English</a>
  </p>
  <p>
    <a href="https://github.com/demon820308/Q-Spark/releases/latest"><img src="https://img.shields.io/github/v/release/demon820308/Q-Spark?color=orange&label=%E7%89%88%E6%9C%AC" alt="最新版本" /></a>
    <img src="https://img.shields.io/badge/%E7%89%88%E6%9C%AC-v0.2.5-green" alt="版本 v0.2.5" />
    <img src="https://img.shields.io/badge/%E5%B9%B3%E5%8F%B0-Windows%20x64-blue" alt="Windows x64" />
    <img src="https://img.shields.io/badge/%E5%BA%95%E5%B1%82%E5%BC%95%E6%93%8E-stable--diffusion.cpp%20(GGML%2FCUDA)-brightgreen" alt="C++ 引擎" />
    <a href="LICENSE"><img src="https://img.shields.io/badge/%E5%BC%80%E6%BA%90%E5%8D%8F%E8%AE%AE-Apache--2.0-blue" alt="Apache-2.0" /></a>
  </p>
</div>

---

## ⚡ 极速推理 · 极致显存 · 全功能创作工作台

| 🚀 秒级极速 · 自由无审查 | 🎨 创作与超分全链路合一 | 🔌 智能体与工作流无缝连接 |
| :--- | :--- | :--- |
| **Qwen-Image-2.1-Turbo** 与 **Z-Image Turbo** 原生本地推理，纯 C++ 底层 GGML/CUDA 架构，主流游戏显卡（8~10G 卡）极速流畅运行。 | 融合**文生图**、**指令编辑**与 **C++ 硬件加速高清超分放大 (2x/4x)**，内置切块进度检测与无损大图拖拽漫游。 | 完整兼容 OpenAI 标准 `/v1/images/generations` HTTP API，完美打通 Dify、Cherry Studio、Chatbox 等 AI 智能体生态。 |

本地工作流 100% 在您自己的硬件上运行。零数据外发、零云端依赖、隐私安全。

---

## 🌟 v0.2.5 核心功能特性

### 1. 🛡️ 架构冲突精准排错与真实错误还原 (True Error Reporting)
- **底层 C++ 报错真实还原**：当底层发生异常退出时，倒序精准提取真实断言行（如 `GGML_ASSERT(ggml_can_repeat)` 或 `scale_nelements`），彻底解决以往“吞没错误”或“张冠李戴误报”的痛点。
- **NVFP4 非标量化精确诊断**：针对 Qwen 3.4B 原始 FP8 混量权重中的 NVFP4 微块量化层（`scale_nelements` 校验失败），提供精确的中文诊断与 `Fix-convert` 修复指引。
- **跨架构维度不匹配智能诊断**：自动识别 Z-Image（2048 维）与 Qwen-Image-2.1（3584 维）文本编码器混用导致的张量广播冲突，给出清晰的成套搭配建议。

### 2. 🎨 VAE 兼容性 A + B 双重保障
- **Layer A 事前预检 (Pre-flight Warning)**：在启动 GPU 任务的第一秒，自动校验所选扩散主模型与 VAE 兼容性；若检测到跨体系错配（如 Z-Image 误选 Qwen VAE，或 Qwen 误选 Flux VAE），立即在日志中给出显眼警示。
- **Layer B 事后异常捕获 (Runtime Catch)**：底层 VAE 解码器若发生崩溃，自动捕获专属异常并给出成套换回建议，彻底防止解码黑图或静默失败。

### 3. 🖥️ 实时日志交互体验优化
- **日志缓冲扩容**：终端日志缓冲容量由 30 行扩展至 120 行，确保前置任务规格与执行阶段步骤绝对不被顶出截断。
- **紧凑追加渲染**：底层报错与排错诊断紧随失败步骤自然追加，不再清空或覆盖既有日志。

### 4. 🔍 硬件加速图像超分辨率放大 (C++ Upscale Engine)
- **原生 C++ 切块超分**：集成 `stable-diffusion.cpp -M upscale` 引擎，支持 2x 细腻平滑保真超分与 4x 极致超分辨率，1~2 秒内输出超清大图。
- **开箱内置首选模型**：便携版开箱内置最优超分模型 `4x-UltraSharp.pth`（约 64MB），开箱即用；支持在 `models/upscale_models` 放入任意第三方超分模型，界面自动识别列出。
- **分块切块 (Tile) 推理实时进度指示**：毫秒级解析底层控制台切块计数（如 `2/9`），独立超分工作区与画廊弹窗均配备动态进度条与运行状态指示。

### 5. 🖼️ 历史画廊全链路超分闭环与元数据继承
- **画廊弹窗一键放大**：画廊详情中直接提供 2x / 4x 放大入口，并配备紧凑的放大模型选择下拉框，两端模型切换双向实时同步。
- **完美继承原始生成参数**：超分图片完整保留源图的 Prompt、负向词、种子、步数、CFG、模型架构与挂载 LoRA，仅追加放大模型与放大倍数，画廊卡片支持“🔍 图像超分放大”标签与筛选。

---

## 📦 快速上手

### 方式一：绿色独立便携版（推荐所有 Win10 / Win11 用户）

无需安装 Python，无需配置环境或下载 pip 依赖包，解压即用！

1. 在 [Releases 发布页面](https://github.com/demon820308/Q-Spark/releases) 下载 **`Q-Spark-0.2.5-windows-x64-portable.zip`**；
2. 解压到电脑上的任意文件夹；
3. 将下载好的模型放入 `models/` 对应子目录中（详见下方 [模型库与目录规范](#模型库与目录规范)）；
4. 双击运行 **`start.bat`**（或 `Q-Spark.exe`）；
5. 浏览器将自动打开交互界面：`http://127.0.0.1:40188`。

---

### 方式二：开发者源码运行

如果您熟悉 Python 环境并希望进行二次开发：

```bash
# 1. 克隆代码仓库
git clone https://github.com/demon820308/Q-Spark.git
cd Q-Spark

# 2. 安装轻量依赖（仅需 Web UI 与 API 组件，无重型 PyTorch 依赖）
pip install -r requirements.txt

# 3. 启动服务
python app.py
```

---

## 📁 模型库与目录规范

Q-Spark 在 `models/` 目录下提供结构化的子目录规范：

```text
models/
├── diffusion_models/   <-- 降噪主模型（DiT / UNet 权重，如 .gguf 或 .safetensors）
├── text_encoders/      <-- 文本编码器（LLM / CLIP 权重，如 .gguf 或 .safetensors）
├── vae/                <-- 变分自编码器（VAE 解码权重，如 .safetensors）
└── loras/              <-- LoRA 风格微调权重（如 .safetensors）
```

> 💡 **ComfyUI 用户一键复用**：如果您本地已安装 ComfyUI，启动后在网页设置中，可直接将模型根目录填写为您现有的 `ComfyUI/models` 路径，无需重复下载！

### 推荐模型套装与下载地址

#### 🌟 套装一：Qwen-Image-2.1-Turbo GGUF 极速免审核版（8~10G 显存首选）
*8步极速推理，去除审核机制，仅需 4~6GB 显存，极低内存消耗。*

| 组件 | 推荐文件名 | 放置子目录 | 下载渠道（含国内高速镜像） |
| :--- | :--- | :--- | :--- |
| **降噪主模型** | `Qwen-Image-2.1-Turbo-AD-Q4_K.gguf` | `models/diffusion_models/` | [HF官方](https://huggingface.co/AtomicChat/Qwen-Image-2.1-Turbo-GGUF) \| [国内镜像](https://hf-mirror.com/AtomicChat/Qwen-Image-2.1-Turbo-GGUF) |
| **文本编码器** | `Qwen-Image-2.1-Turbo-Abliterated-Uncensored-AD-Q4_K.gguf` | `models/text_encoders/` | [HF官方](https://huggingface.co/AtomicChat/Qwen-Image-2.1-Turbo-Uncensored-GGUF) \| [国内镜像](https://hf-mirror.com/AtomicChat/Qwen-Image-2.1-Turbo-Uncensored-GGUF) |
| **变分自编码器** | `qwen_image_2.1_vae_bf16.safetensors` | `models/vae/` | [HF官方](https://huggingface.co/Qwen/Qwen-Image-2.1) \| [国内镜像](https://hf-mirror.com/Qwen/Qwen-Image-2.1) |

#### 🔥 套装二：Qwen-Image-2.1-UC 免审核 INT8 完整量化套装（abenzerps 推荐）
*纯 Safetensors 原生量化格式，免审核（Uncensored）降噪核心，搭配 INT8 文本编码器与 BF16 VAE，画质与生成表现极其出色。*

| 组件 | 推荐文件名 | 放置子目录 | 下载渠道 |
| :--- | :--- | :--- | :--- |
| **降噪主模型** | `qwen-image-2.1-UC-int8_convrot.safetensors` | `models/diffusion_models/` | [HF官方](https://huggingface.co/abenzerps/Qwen-Image-2.1-Uncensored-Quantized/tree/main) \| [国内镜像](https://hf-mirror.com/abenzerps/Qwen-Image-2.1-Uncensored-Quantized) |
| **文本编码器** | `qwen3vl_8b_int8_convrot.safetensors` | `models/text_encoders/` | [HF官方](https://huggingface.co/abenzerps/Qwen-Image-2.1-Uncensored-Quantized/tree/main) \| [国内镜像](https://hf-mirror.com/abenzerps/Qwen-Image-2.1-Uncensored-Quantized) |
| **变分自编码器** | `qwen_image_2.1_vae_bf16.safetensors` | `models/vae/` | [HF官方](https://huggingface.co/abenzerps/Qwen-Image-2.1-Uncensored-Quantized/tree/main) \| [国内镜像](https://hf-mirror.com/abenzerps/Qwen-Image-2.1-Uncensored-Quantized) |

#### 🚀 套装三：Qwen-Image-2.1-Turbo 6步动态加速版（INT8 Safetensors）
*搭配 Viggle 分辨率动态调度算法，只需 6 步即可生成细腻大图。*

| 组件 | 推荐文件名 | 放置子目录 | 下载渠道 |
| :--- | :--- | :--- | :--- |
| **降噪主模型** | `Qwen-Image-2.1-viggle-turbo-v0.3-6step-int8_convrot.safetensors` | `models/diffusion_models/` | [HF官方](https://huggingface.co/Viggle/Qwen-Image-2.1-viggle-turbo) \| [国内镜像](https://hf-mirror.com/Viggle/Qwen-Image-2.1-viggle-turbo) |
| **文本编码器** | `qwen3vl_8b_int8_convrot.safetensors` | `models/text_encoders/` | [HF官方](https://huggingface.co/Comfy-Org/Qwen-Image-2.1) \| [国内镜像](https://hf-mirror.com/Comfy-Org/Qwen-Image-2.1) |
| **变分自编码器** | `qwen_image_2.1_vae_bf16.safetensors` | `models/vae/` | 同套装一 |

#### 🎨 套装四：Z-Image Turbo 体系（阿里单流 S3-DiT 架构）
*阿里通义开源轻量新架构，推荐步数 8~9 步，采样器 `euler`。*

| 组件 | 推荐文件名 | 放置子目录 | 下载渠道 |
| :--- | :--- | :--- | :--- |
| **降噪主模型** | `z_image_turbo_int8_convrot.safetensors` | `models/diffusion_models/` | [HF官方](https://huggingface.co/Comfy-Org/z_image_turbo) \| [国内镜像](https://hf-mirror.com/Comfy-Org/z_image_turbo) |
| **文本编码器** | `qwen_3_4b_fp8_mixed_fixed.safetensors` (修复版) 或 `qwen_3_4b.safetensors` | `models/text_encoders/` | [HF官方原版](https://huggingface.co/Comfy-Org/z_image_turbo) \| [国内镜像](https://hf-mirror.com/Comfy-Org/z_image_turbo) |
| **变分自编码器** | `ae.safetensors` (Flux VAE) | `models/vae/` | [HF官方](https://huggingface.co/Comfy-Org/z_image_turbo) \| [国内镜像](https://hf-mirror.com/Comfy-Org/z_image_turbo) |

> 🛠️ **Z-Image 文本编码器修复指南（Fix-convert 说明）**
> - **为什么要用 Fix-convert？**  
>   社区和 Comfy-Org 早期分发的 `qwen_3_4b_fp8_mixed.safetensors` 中，包含 12 个带有非标 **NVFP4 2D 分块量化**的注意力层（含有 `.comfy_quant` 与 `weight_scale_2`）。底层的纯 C++ 推理引擎（`stable-diffusion.cpp`）不支持这种非标 NVFP4 格式，直接载入会报错或生图黑屏。  
>   通过项目内置的 `Fix-convert` 工具，在 GPU 上将这 12 个非标层反量化还原为标准 `bfloat16`（其余标准 FP8 层原样保留），即可生成能被完全兼容解析的标准模型 `qwen_3_4b_fp8_mixed_fixed.safetensors`。
> - **使用方法：**
>   1. 将待修复的 `qwen_3_4b_fp8_mixed.safetensors` 放入项目中的 `Fix-convert/` 文件夹中（或直接拖拽到 `一键修复.bat` 上）；
>   2. 双击运行 `Fix-convert/一键修复.bat`；
>   3. 稍候片刻，同目录下会自动生成修复后的 `qwen_3_4b_fp8_mixed_fixed.safetensors`；
>   4. 将生成的文件放入 `models/text_encoders/` 目录中即可直接在控制台调用。


---

## 🤖 Agent API 接口（完全兼容 OpenAI 规范）

Q-Spark 内置了标准的 HTTP 服务接口，可无缝对接任何支持 OpenAI DALL-E / 图片生成的客户端：

* **接口地址**：`http://127.0.0.1:40188/v1/images/generations`
* **请求方式**：`POST`
* **Content-Type**：`application/json`

### Python 调用示例

```python
import requests

url = "http://127.0.0.1:40188/v1/images/generations"
payload = {
    "prompt": "赛博朋克风格猫咪，佩戴发光全息护目镜，8k超清细节 --ar 16:9",
    "size": "1360x768",
    "steps": 8,
    "response_format": "url"  # 支持 "url" 或 "b64_json"
}

resp = requests.post(url, json=payload).json()
print("生成图片地址:", resp["data"][0]["url"])
```

### 第三方客户端配置（Dify / Cherry Studio 等）
在智能体平台中添加模型供应商：
1. **接口类型**：OpenAI（或自定义 OpenAI 兼容接口）
2. **Base URL**：`http://127.0.0.1:40188/v1`
3. **API Key**：`sk-any`（任意填写即可）
4. **模型名称**：`q-spark`（或默认）

---

## 🧩 通用 AI Agent 技能生态（所有智能体通用指南）

Q-Spark 内置了**面向所有 AI Agent / 智能体 / 编码助手**的标准生图技能生态：

* **核心技能包目录**：[`skills/qspark/`](skills/qspark/)（包含通用能力说明书 `SKILL.md` 与跨平台执行脚本 `scripts/generate.py`）
* **项目工作区内嵌**：[`.agents/skills/qspark/`](.agents/skills/qspark/)

### 为什么所有 Agent 都推荐使用此 Skill？
1. **保留大模型思考大脑**：不用把 Agent 的主模型硬切为生图模型，Agent 依然使用 Claude、GPT-4o、Gemini 等强推理大模型写代码、拆解任务，仅在需要插图时把 Q-Spark 当作画笔工具；
2. **单一可信源 (Single Source of Truth)**：出图模型完全由本地 `config.json` 动态控制（Z-Image 或 Qwen 自由切换），Agent 绝不硬编码模型名字；
3. **零额外环境依赖**：`generate.py` 纯 Python 标准库编写，任何具备终端执行环境的 Agent 均可 1 秒调起；
4. **全自动闭环输出**：出图后自动返回图片物理路径与 Markdown 格式预览链接 `![image](file:///...)`，无缝嵌入各客户端对话流。

---

### 各类型 Agent 的安装与集成方法

#### 1. 终端与代码型 Agent（Claude Code, Cursor, Windsurf, Antigravity, Roo Code, Aider 等）
这类 Agent 支持在终端执行命令或读取工作区规则：
* **免安装直接调用**：引导 Agent 读取 [`skills/qspark/SKILL.md`](skills/qspark/SKILL.md)，Agent 在需要生图时直接执行：
  ```powershell
  python "skills/qspark/scripts/generate.py" --prompt "赛博朋克风格机甲猫咪，8k超清" --size "1360x768"
  ```
* **工作区自动发现**：在克隆或打开本项目时，智能体环境会自动发现 `.agents/skills/qspark`，无需任何配置，直接对 Agent 说：
  > *“帮我画一张赛博朋克夜景插图，16:9”*
* **全局安装（跨所有项目随时可用）**：
  * **Windows**：
    ```powershell
    Copy-Item -Path "skills\qspark" -Destination "$env:USERPROFILE\.gemini\config\skills\qspark" -Recurse -Force
    ```
  * **Linux / macOS**：
    ```bash
    cp -r skills/qspark ~/.gemini/config/skills/qspark
    ```

#### 2. 自定义 Python 智能体与框架（LangChain, AutoGen, CrewAI, LlamaIndex 等）
将 `skills/qspark/scripts/generate.py` 包装为工具函数（Tool / Function Call）：
```python
import subprocess
import json

def generate_image_tool(prompt: str, size: str = "1024x1024") -> str:
    """调用本地 Q-Spark 引擎生成图片并返回本地文件路径"""
    cmd = ["python", "skills/qspark/scripts/generate.py", "--prompt", prompt, "--size", size]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout  # 包含本地路径与 Markdown 预览
```

#### 3. 平台型智能体与对话客户端（Dify, FastGPT, Coze, Cherry Studio, Chatbox）
对于通过标准 HTTP 请求交互的智能体工作流平台：
* **接口协议**：OpenAI Compatible
* **Base URL**：`http://127.0.0.1:40188/v1`
* **API Key**：`sk-any`（填任意字符串）
* **接口路径**：`POST /v1/images/generations` 或 `POST /v1/chat/completions`

## 🛠️ 技术底座与致谢

* **底层推理引擎**：[stable-diffusion.cpp](https://github.com/leejet/stable-diffusion.cpp) (纯 C++ GGML/CUDA 移植)
* **基座开源模型**：[Qwen-Image](https://github.com/QwenLM/Qwen-Image) & [Z-Image](https://huggingface.co/Tongyi-MAI/Z-Image-Turbo)
* **前端架构**：原生 Vanilla HTML5 / CSS3 / JavaScript 单页应用（零重型框架负担）
* **API 服务框架**：[FastAPI](https://github.com/fastapi/fastapi) & [Uvicorn](https://github.com/encode/uvicorn)

---

## 📄 开源许可

本项目基于 [Apache-2.0 开源协议](LICENSE)。
