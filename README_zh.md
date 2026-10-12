<div align="center">
  <img src="assets/logo.png" alt="Q-Spark" width="100" />
  <h1>Q-Spark 生图控制台</h1>
  <p><strong>基于 stable-diffusion.cpp C++ 原生引擎的轻量高性能本地 AI 生图工作室，支持兼容 OpenAI 的 Agent API。</strong></p>
  <p>
    <a href="https://github.com/demon820308/Q-Spark/releases/latest">下载便携版 v0.2.1</a> ·
    <a href="#核心功能特性">核心特性</a> ·
    <a href="#快速上手">快速上手</a> ·
    <a href="#模型库与目录规范">模型库指引</a> ·
    <a href="#agent-api-接口">Agent API</a> ·
    <a href="README.md">English</a>
  </p>
  <p>
    <a href="https://github.com/demon820308/Q-Spark/releases/latest"><img src="https://img.shields.io/github/v/release/demon820308/Q-Spark?color=orange&label=%E7%89%88%E6%9C%AC" alt="最新版本" /></a>
    <img src="https://img.shields.io/badge/%E7%89%88%E6%9C%AC-v0.2.1-green" alt="版本 v0.2.1" />
    <img src="https://img.shields.io/badge/%E5%B9%B3%E5%8F%B0-Windows%20x64-blue" alt="Windows x64" />
    <img src="https://img.shields.io/badge/%E5%BA%95%E5%B1%82%E5%BC%95%E6%93%8E-stable--diffusion.cpp%20(GGML%2FCUDA)-brightgreen" alt="C++ 引擎" />
    <a href="LICENSE"><img src="https://img.shields.io/badge/%E5%BC%80%E6%BA%90%E5%8D%8F%E8%AE%AE-Apache--2.0-blue" alt="Apache-2.0" /></a>
  </p>
</div>

---

## ⚡ 极速推理 · 极致显存 · 全功能创作工作台

| 🚀 秒级极速 · 自由无审查 | 🎨 创作工作台三态合一 | 🔌 智能体与工作流无缝连接 |
| :--- | :--- | :--- |
| **Qwen-Image-2.1-Turbo** (6~8步极速) 与 **Z-Image Turbo** (8~9步) 原生本地推理，纯 C++ 底层 GGML/CUDA 架构，主流游戏显卡（RTX 3060 / 3080 / 4060 等 8~10G 卡）流畅运行。 | 单一交互工作台完美融合**文生图 (txt2img)** 与 **多模态图像指令编辑 (Image Edit)**，极简高效，参数无缝流转。 | 完整兼容 OpenAI 标准 `/v1/images/generations` HTTP API，支持智能比例解析，完美打通 Dify、Cherry Studio、Chatbox 等 AI 智能体生态。 |

本地工作流 100% 在您自己的硬件上运行。零数据外发、零云端依赖、隐私安全。

---

## 🌟 v0.2.1 核心功能特性

### 1. 🎨 创作工作台多模态进阶（模式隔离，智能流转）
- **文生图 (txt2img)**：零底图纯文本极速出图，模型特征步数自适应，支持采样步数、随机种子、CFG 细致调节。
- **图像指令编辑 (Image Edit)**：基于视觉投射器（Vision Projector）的纯净空噪声起步编辑模式，摆脱传统图生图底图噪波干扰，忠实遵循自然语言修改指令。
- **多图参考与视觉 Token 智能映射**：支持最多 3 张参考图；提示词中输入的“图1”、“图2”、“图片1”等自然语言，系统自动识别并映射为 Qwen 原生视觉 Token `<image1>` / `<image2>`。
- **实时任务中断 (⏹️ 停止任务)**：前端提供一键终止按钮，调用 `/api/task/stop` 毫秒级杀灭底层生成子进程，即刻释放 GPU 显存。

### 2. 🏷️ 多 LoRA 动态挂载管理器
- 自动扫描识别 `models/loras/` 下的 safetensors 权重。
- 下拉选择与即时挂载，每个 LoRA 独立调节权重（0.1 ~ 2.0），自动展开提示词宏并传参至底层 CLI。

### 3. 🖼️ 全功能沉浸式历史画廊 2.0
- **伴生元数据永久保存**：每张图片生成均附带独立 Sidecar JSON，完整记录提示词、负面词、模型组合、LoRA 挂载列表、步数、CFG、耗时与模式标记。
- **工作流一键闭环流转**：
  - `⚡ 参数重绘 / 复用`：一键将历史参数自动回填至创作表单；
  - `🔄 垫图`：一键将历史图送入参考图区域进行二次编辑。
- **方案 A 沉浸式原图查看器**：全屏大图预览，支持原图 1:1 物理像素与适应屏幕双态缩放切换，支持 ESC 键或点击遮罩随时关闭。

### 4. 🧠 硬件监控与自适应调度
- **硬件实时监控**：毫秒级采集 GPU 显存 (VRAM)、系统内存 (RAM) 与 CPU 占用率，提供动态色条状态预警。
- **智能步数与调度器自适应**：依据加载模型自动匹配最佳步数（Viggle Turbo 自动 6 步并挂载动态分辨率 Sigmas，Turbo/Z-Image 自动 8 步，标准模型 25 步）。
- **三种显存管理策略**：
  - **即用即走（On-Demand）**：冷启动生成，任务结束显存 0MB 闲置占用（8~10GB 显卡强烈推荐）；
  - **智能休眠（Auto-Unload）**：5 分钟闲置自动卸载显存（需 16GB+ 显存）；
  - **显存常驻（Always-On）**：后台常驻模型，秒级响应（需 16GB+ 显存）。

---

## 📦 快速上手

### 方式一：绿色独立便携版（推荐所有 Win10 / Win11 用户）

无需安装 Python，无需配置环境或下载 pip 依赖包，解压即用！

1. 在 [Releases 发布页面](https://github.com/demon820308/Q-Spark/releases) 下载 **`Q-Spark-0.2.1-windows-x64-portable.zip`**；
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

## 🛠️ 技术底座与致谢

* **底层推理引擎**：[stable-diffusion.cpp](https://github.com/leejet/stable-diffusion.cpp) (纯 C++ GGML/CUDA 移植)
* **基座开源模型**：[Qwen-Image](https://github.com/QwenLM/Qwen-Image) & [Z-Image](https://huggingface.co/Tongyi-MAI/Z-Image-Turbo)
* **前端架构**：原生 Vanilla HTML5 / CSS3 / JavaScript 单页应用（零重型框架负担）
* **API 服务框架**：[FastAPI](https://github.com/fastapi/fastapi) & [Uvicorn](https://github.com/encode/uvicorn)

---

## 📄 开源许可

本项目基于 [Apache-2.0 开源协议](LICENSE)。
