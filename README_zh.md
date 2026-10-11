<div align="center">
  <img src="assets/logo.png" alt="Q-Spark" width="100" />
  <h1>Q-Spark 生图控制台</h1>
  <p><strong>基于 stable-diffusion.cpp C++ 原生引擎的轻量高性能本地 AI 生图工作室，支持兼容 OpenAI 的 Agent API。</strong></p>
  <p>
    <a href="https://github.com/demon820308/Q-Spark/releases/latest">下载便携版</a> ·
    <a href="#快速上手">快速上手</a> ·
    <a href="#模型库与目录规范">模型库指引</a> ·
    <a href="#agent-api-接口">Agent API</a> ·
    <a href="README.md">English</a>
  </p>
  <p>
    <a href="https://github.com/demon820308/Q-Spark/releases/latest"><img src="https://img.shields.io/github/v/release/demon820308/Q-Spark?color=orange&label=%E7%89%88%E6%9C%AC" alt="最新版本" /></a>
    <img src="https://img.shields.io/badge/%E5%B9%B3%E5%8F%B0-Windows%20x64-blue" alt="Windows x64" />
    <img src="https://img.shields.io/badge/%E5%BA%95%E5%B1%82%E5%BC%95%E6%93%8E-stable--diffusion.cpp%20(GGML%2FCUDA)-brightgreen" alt="C++ 引擎" />
    <a href="LICENSE"><img src="https://img.shields.io/badge/%E5%BC%80%E6%BA%90%E5%8D%8F%E8%AE%AE-Apache--2.0-blue" alt="Apache-2.0" /></a>
  </p>
</div>

---

## ⚡ 极速推理 · 极致显存 · 无缝生态连接

| 🚀 秒级极速 · 自由无审查 | 🧠 极致显存优化 (4~10GB) | 🔌 智能体与工作流无缝连接 |
| :--- | :--- | :--- |
| **Qwen-Image-2.1-Turbo** (6~8步极速) 与 **Z-Image Turbo** (8~9步) 原生本地推理，画质无妥协。 | 纯 C++ 底层 GGML/CUDA 架构，极速释放算力，主流游戏显卡（RTX 3060 / 3080 / 4060 等）畅跑。 | 完整兼容 OpenAI 标准 `/v1/images/generations` HTTP API，完美打通 Dify、Cherry Studio、Chatbox 等 AI 智能体生态。 |

本地工作流 100% 在您自己的硬件上运行。零数据外发、零云端依赖、隐私安全。

---

## 📦 快速上手

### 方式一：绿色独立便携版（推荐所有 Win10 / Win11 用户）

无需安装 Python，无需配置环境或下载 pip 依赖包，解压即用！

1. 在 [Releases 发布页面](https://github.com/demon820308/Q-Spark/releases) 下载 **`Q-Spark-0.1.0-windows-x64-portable.zip`**；
2. 解压到电脑上的任意文件夹；
3. 将下载好的模型放入 `models/` 对应子目录中（详见下方 [模型库与目录规范](#模型库与目录规范)）；
4. 双击运行 **`start.bat`**（或运行 `创建桌面快捷方式.bat` 生成桌面图标后双击）；
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

Q-Spark 在 `models/` 目录下提供标准的三层目录结构：

```text
models/
├── diffusion_models/   <-- 降噪主模型（DiT / UNet 权重，如 .gguf 或 .safetensors）
├── text_encoders/      <-- 文本编码器（LLM / CLIP 权重，如 .gguf 或 .safetensors）
└── vae/                <-- 变分自编码器（VAE 解码权重，如 .safetensors）
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

#### 🚀 套装二：Qwen-Image-2.1-Turbo 6步动态加速版（INT8 Safetensors）
*搭配 Viggle 分辨率动态调度算法，只需 6 步即可生成细腻大图。*

| 组件 | 推荐文件名 | 放置子目录 | 下载渠道 |
| :--- | :--- | :--- | :--- |
| **降噪主模型** | `Qwen-Image-2.1-viggle-turbo-v0.3-6step-int8_convrot.safetensors` | `models/diffusion_models/` | [HF官方](https://huggingface.co/city96/Qwen-Image-2.1-Turbo-gguf) \| [国内镜像](https://hf-mirror.com/city96/Qwen-Image-2.1-Turbo-gguf) |
| **文本编码器** | `qwen3vl_8b_int8_convrot.safetensors` | `models/text_encoders/` | [HF官方](https://huggingface.co/city96/Qwen-Image-2.1-Turbo-gguf) \| [国内镜像](https://hf-mirror.com/city96/Qwen-Image-2.1-Turbo-gguf) |
| **变分自编码器** | `qwen_image_2.1_vae_bf16.safetensors` | `models/vae/` | 同套装一 |

#### 🎨 套装三：Z-Image Turbo 体系（阿里单流 S3-DiT 架构）
*阿里通义开源轻量新架构，推荐步数 8~9 步，采样器 `euler`，调度器 `simple`。*

| 组件 | 推荐文件名 | 放置子目录 | 下载渠道 |
| :--- | :--- | :--- | :--- |
| **降噪主模型** | `z_image_turbo_int8_convrot.safetensors` | `models/diffusion_models/` | [HF官方](https://huggingface.co/Comfy-Org/z_image_turbo) \| [国内镜像](https://hf-mirror.com/Comfy-Org/z_image_turbo) |
| **文本编码器** | `qwen_3_4b_fixed.safetensors` 或 `qwen_3_4b.safetensors` | `models/text_encoders/` | [HF官方原版](https://huggingface.co/Comfy-Org/z_image_turbo) *(注：请勿使用带 NVFP4 2D分块量化的实验版)* |
| **变分自编码器** | `ae.safetensors` (Flux VAE) | `models/vae/` | [HF官方](https://huggingface.co/Comfy-Org/z_image_turbo) |

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
    "prompt": "赛博朋克风格猫咪，佩戴发光全息护目镜，8k超清细节",
    "size": "1024x1024",
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
* **Web UI 界面**：[Gradio](https://github.com/gradio-app/gradio) (采用定制 Claude Dark 主题)
* **API 服务框架**：[FastAPI](https://github.com/fastapi/fastapi) & [Uvicorn](https://github.com/encode/uvicorn)

## 📄 开源许可

本项目基于 [Apache-2.0 开源协议](LICENSE)。
