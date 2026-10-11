<div align="center">
  <img src="assets/logo.png" alt="Q-Spark" width="100" />
  <h1>Q-Spark Studio</h1>
  <p><strong>High-performance, lightweight local AI image generation studio powered by stable-diffusion.cpp with OpenAI-compatible Agent API.</strong></p>
  <p>
    <a href="https://github.com/demon820308/Q-Spark/releases/latest">Download Portable</a> ·
    <a href="#quick-start">Quick Start</a> ·
    <a href="#models-catalog">Models Catalog</a> ·
    <a href="#agent-api">Agent API</a> ·
    <a href="README_zh.md">简体中文</a>
  </p>
  <p>
    <a href="https://github.com/demon820308/Q-Spark/releases/latest"><img src="https://img.shields.io/github/v/release/demon820308/Q-Spark?color=orange&label=Release" alt="Latest Release" /></a>
    <img src="https://img.shields.io/badge/Platform-Windows%20x64-blue" alt="Windows x64" />
    <img src="https://img.shields.io/badge/Engine-stable--diffusion.cpp%20(GGML%2FCUDA)-brightgreen" alt="C++ Engine" />
    <a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache--2.0-blue" alt="Apache-2.0" /></a>
  </p>
</div>

---

## ⚡ High Performance. Low VRAM. Agent Connected.

| 🚀 Blazing Fast & Uncensored | 🧠 Memory Efficient (4~10GB) | 🔌 Agent & Workflow Ready |
| :--- | :--- | :--- |
| **Qwen-Image-2.1-Turbo** (6~8 steps) & **Z-Image Turbo** (8~9 steps) local inference with uncompromised quality. | Native pure C++ GGML CUDA backend. Seamlessly runs on consumer GPUs (RTX 3060 / 3080 / 4060). | Fully OpenAI-compatible `/v1/images/generations` HTTP API for Dify, Cherry Studio, Chatbox, and multi-agent systems. |

Local workflows run 100% on your own hardware. Zero telemetry, zero cloud dependency, complete privacy.

---

## 📦 Quick Start

### Option 1: Standalone Portable Package (Recommended for Windows 10 / 11)

No Python installation required. No dependencies or build tools needed.

1. Download **`Q-Spark-0.1.0-windows-x64-portable.zip`** from [Releases](https://github.com/demon820308/Q-Spark/releases).
2. Extract the archive to any folder on your computer.
3. Download your preferred models and place them into the `models/` directory (see [Models Catalog](#models-catalog) below).
4. Double-click **`start.bat`** (or run `创建桌面快捷方式.bat` to create a Desktop shortcut).
5. The Web UI will automatically open in your browser at `http://127.0.0.1:40188`.

---

### Option 2: Run from Source

If you prefer using your existing Python environment:

```bash
# 1. Clone the repository
git clone https://github.com/demon820308/Q-Spark.git
cd Q-Spark

# 2. Install lightweight dependencies
pip install -r requirements.txt

# 3. Start the server
python app.py
```

---

## 📁 Models Catalog & Directory Structure

Q-Spark organizes model files into three clean subdirectories inside `models/`:

```text
models/
├── diffusion_models/   <-- Diffusion Backbone (DiT / UNet, .gguf or .safetensors)
├── text_encoders/      <-- Text Encoders (LLM / CLIP, .gguf or .safetensors)
└── vae/                <-- Variational Autoencoders (.safetensors)
```

> 💡 **Tip for ComfyUI Users**: If you already have ComfyUI installed, you can simply point the model root directory in the Web UI to your existing `ComfyUI/models` path without re-downloading!

### Recommended Presets

#### 🌟 Preset 1: Qwen-Image-2.1-Turbo GGUF (Uncensored / 8-10G VRAM Best Pick)
*Ultra-fast 8-step inference with abliterated prompt censorship filter.*

| Component | File Name | Destination | Download Links |
| :--- | :--- | :--- | :--- |
| **Diffusion Model** | `Qwen-Image-2.1-Turbo-AD-Q4_K.gguf` | `models/diffusion_models/` | [HuggingFace](https://huggingface.co/AtomicChat/Qwen-Image-2.1-Turbo-GGUF) \| [Mirror (CN)](https://hf-mirror.com/AtomicChat/Qwen-Image-2.1-Turbo-GGUF) |
| **Text Encoder** | `Qwen-Image-2.1-Turbo-Abliterated-Uncensored-AD-Q4_K.gguf` | `models/text_encoders/` | [HuggingFace](https://huggingface.co/AtomicChat/Qwen-Image-2.1-Turbo-Uncensored-GGUF) \| [Mirror (CN)](https://hf-mirror.com/AtomicChat/Qwen-Image-2.1-Turbo-Uncensored-GGUF) |
| **VAE** | `qwen_image_2.1_vae_bf16.safetensors` | `models/vae/` | [HuggingFace](https://huggingface.co/Qwen/Qwen-Image-2.1) \| [Mirror (CN)](https://hf-mirror.com/Qwen/Qwen-Image-2.1) |

#### 🚀 Preset 2: Qwen-Image-2.1-Turbo 6-Step Dynamic (INT8 Safetensors)
*Powered by dynamic Viggle resolution-shifted schedule.*

| Component | File Name | Destination | Download Links |
| :--- | :--- | :--- | :--- |
| **Diffusion Model** | `Qwen-Image-2.1-viggle-turbo-v0.3-6step-int8_convrot.safetensors` | `models/diffusion_models/` | [HuggingFace](https://huggingface.co/city96/Qwen-Image-2.1-Turbo-gguf) \| [Mirror (CN)](https://hf-mirror.com/city96/Qwen-Image-2.1-Turbo-gguf) |
| **Text Encoder** | `qwen3vl_8b_int8_convrot.safetensors` | `models/text_encoders/` | [HuggingFace](https://huggingface.co/city96/Qwen-Image-2.1-Turbo-gguf) \| [Mirror (CN)](https://hf-mirror.com/city96/Qwen-Image-2.1-Turbo-gguf) |
| **VAE** | `qwen_image_2.1_vae_bf16.safetensors` | `models/vae/` | Same as Preset 1 |

#### 🎨 Preset 3: Z-Image Turbo Architecture (Single-Stream S3-DiT)
*Alibaba Tongyi-MAI's new architecture, 8~9 steps Euler generation.*

| Component | File Name | Destination | Download Links |
| :--- | :--- | :--- | :--- |
| **Diffusion Model** | `z_image_turbo_int8_convrot.safetensors` | `models/diffusion_models/` | [HuggingFace](https://huggingface.co/Comfy-Org/z_image_turbo) \| [Mirror (CN)](https://hf-mirror.com/Comfy-Org/z_image_turbo) |
| **Text Encoder** | `qwen_3_4b_fixed.safetensors` or `qwen_3_4b.safetensors` | `models/text_encoders/` | [HuggingFace](https://huggingface.co/Comfy-Org/z_image_turbo) *(Note: avoid experimental NVFP4 block-quantized versions)* |
| **VAE** | `ae.safetensors` (Flux VAE) | `models/vae/` | [HuggingFace](https://huggingface.co/Comfy-Org/z_image_turbo) |

---

## 🤖 Agent API (OpenAI Compatible)

Q-Spark features a high-performance HTTP endpoint compliant with the standard OpenAI image generation protocol:

* **Endpoint**: `http://127.0.0.1:40188/v1/images/generations`
* **Method**: `POST`
* **Content-Type**: `application/json`

### Python Example

```python
import requests

url = "http://127.0.0.1:40188/v1/images/generations"
payload = {
    "prompt": "A cyberpunk kitten wearing neon holographic goggles, 8k masterpiece",
    "size": "1024x1024",
    "steps": 8,
    "response_format": "url"  # or "b64_json"
}

response = requests.post(url, json=payload).json()
image_url = response["data"][0]["url"]
print(f"Image generated: {image_url}")
```

### Multi-Agent Integration (Dify / Cherry Studio)
In your agent platform settings:
1. Provider: **OpenAI** (or Custom OpenAI Compatible)
2. Base URL: `http://127.0.0.1:40188/v1`
3. API Key: `sk-any` (any placeholder string)
4. Model Name: `q-spark` (or leave default)

---

## 🛠️ Tech Stack & Acknowledgements

* **Inference Engine**: [stable-diffusion.cpp](https://github.com/leejet/stable-diffusion.cpp) (GGML C++ CUDA)
* **Foundational Models**: [Qwen-Image](https://github.com/QwenLM/Qwen-Image) & [Z-Image](https://huggingface.co/Tongyi-MAI/Z-Image-Turbo)
* **Frontend UI**: [Gradio](https://github.com/gradio-app/gradio) with Claude Dark theme
* **API Framework**: [FastAPI](https://github.com/fastapi/fastapi) & [Uvicorn](https://github.com/encode/uvicorn)

## 📄 License

This project is licensed under the [Apache-2.0 License](LICENSE).
