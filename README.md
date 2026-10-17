<div align="center">
  <img src="assets/logo.png" alt="Q-Spark" width="100" />
  <h1>Q-Spark Studio</h1>
  <p><strong>High-performance, lightweight local AI image generation studio powered by stable-diffusion.cpp with OpenAI-compatible Agent API.</strong></p>
  <p>
    <a href="https://github.com/demon820308/Q-Spark/releases/latest">Download Portable v0.2.7</a> ·
    <a href="#key-features">Key Features</a> ·
    <a href="#quick-start">Quick Start</a> ·
    <a href="#models-catalog">Models Catalog</a> ·
    <a href="#agent-api">Agent API</a> ·
    <a href="README_zh.md">简体中文</a>
  </p>
  <p>
    <a href="https://github.com/demon820308/Q-Spark/releases/latest"><img src="https://img.shields.io/github/v/release/demon820308/Q-Spark?color=orange&label=Release" alt="Latest Release" /></a>
    <img src="https://img.shields.io/badge/Version-v0.2.7-green" alt="Version v0.2.7" />
    <img src="https://img.shields.io/badge/Platform-Windows%20x64-blue" alt="Windows x64" />
    <img src="https://img.shields.io/badge/Engine-stable--diffusion.cpp%20(GGML%2FCUDA)-brightgreen" alt="C++ Engine" />
    <a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache--2.0-blue" alt="Apache-2.0" /></a>
  </p>
</div>

---

## ⚡ High Performance. Low VRAM. All-in-One Studio.

| 🚀 Blazing Fast & Uncensored | 🎨 Creation & Upscale Pipeline | 🔌 Agent & Workflow Ready |
| :--- | :--- | :--- |
| **Qwen-Image-2.1-Turbo**, **Krea-2 Turbo** & **Z-Image Turbo** local inference. Native pure C++ GGML CUDA engine running comfortably on 8~10GB GPUs (RTX 3060 / 3080 / 4060). | Seamless integration of **Text-to-Image**, **Instruction Editing**, and **C++ Hardware-Accelerated Upscaling (2x/4x)** with real-time tile tracking and infinite drag-to-pan preview. | Standard OpenAI-compatible `/v1/images/generations` HTTP API for Dify, Cherry Studio, Chatbox, and multi-agent workflows. |

Local workflows run 100% on your own hardware. Zero telemetry, zero cloud dependency, complete privacy.

---

## 🌟 Key Features in v0.2.7

### 1. 🧠 Qwen3-VL Text Encoder Millisecond Auto-Alignment (Self-Healing)
- **Zero-Friction Zero-Crash Pipeline**: Reads safetensors header JSON metadata in milliseconds (without loading full weights into memory); automatically detects raw HuggingFace `model.language_model.` key prefixes.
- **Silent On-the-Fly Normalization**: Automatically converts and caches `_fixed.safetensors` on first run, eliminating `embed_tokens.weight not in model metadata` assertion crashes with zero user intervention.

### 2. ⚡ Krea-2 Turbo Architecture Native Support (12B MMDiT)
- **High-Aesthetic 12B Foundation**: Full native support for Krea AI's official open-source 12B single-stream MMDiT (`krea2_turbo_int8_convrot.safetensors`).
- **Rapid 8-Step Distillation**: Out-of-the-box support for 8-step Euler / simple schedule, natively paired with auto-aligned `qwen3vl_4b_int8_convrot.safetensors` and `qwen_image_vae.safetensors`.

### 3. 📖 Visual Interactive "Model Matching Guide" Modal
- **Direct Web UI Integration**: Instant one-click guide accessible directly from the top navigation bar.
- **Card-Based Recipe Cards**: Visually displays recipes and step suggestions across 6 mainstream suites: Qwen 2.1 Turbo GGUF, Qwen 2.1 UC INT8, Krea-2 Turbo, Z-Image Turbo, Qwen 2.1 Native, and Flux.1/2.

### 4. 🎯 Precision Turbo Scheduling & Tensor Diagnostics
- **Decoupled Sigma Curves**: Isolates Qwen 2.1 specific 8-step sigmas from other Turbo models (such as Krea-2 and Viggle) to ensure optimal sampling fidelity.
- **Smart Tensor Metadata Diagnostics**: Catches non-standard tensor naming and immediately outputs precise pairing and fix advice.

### 5. 🛠️ Fix-convert Tool Suite Expansion
- **Stand-alone Offline Conversion**: Added `Fix-convert/convert_qwen3vl.py` and `一键修复_Qwen3VL.bat` for offline drag-and-drop batch conversion and redistribution.

---

## 📦 Quick Start

### Option 1: Standalone Portable Package (Recommended for Windows 10 / 11)

No Python installation required. No dependencies or build tools needed.

1. Download **`Q-Spark-0.2.7-windows-x64-portable.zip`** from [Releases](https://github.com/demon820308/Q-Spark/releases).
2. Extract the archive to any folder on your computer.
3. Download your preferred models and place them into the `models/` directory (see [Models Catalog](#models-catalog) below).
4. Double-click **`start.bat`** (or `Q-Spark.exe`).
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

Q-Spark organizes model files into structured subdirectories inside `models/`:

```text
models/
├── diffusion_models/   <-- Diffusion Backbone (DiT / UNet, .gguf or .safetensors)
├── text_encoders/      <-- Text Encoders (LLM / CLIP, .gguf or .safetensors)
├── vae/                <-- Variational Autoencoders (.safetensors)
└── loras/              <-- LoRA weights (.safetensors)
```

> 💡 **Tip for ComfyUI Users**: If you already have ComfyUI installed, you can simply point the model root directory in the Web UI to your existing `ComfyUI/models` path without re-downloading!

### Recommended Model Presets

#### 🌟 Preset 1: Qwen-Image-2.1-Turbo GGUF (Uncensored / 8-10G VRAM Best Pick)
*Ultra-fast 8-step inference with abliterated prompt censorship filter.*

| Component | File Name | Destination | Download Links |
| :--- | :--- | :--- | :--- |
| **Diffusion Model** | `Qwen-Image-2.1-Turbo-AD-Q4_K.gguf` | `models/diffusion_models/` | [HuggingFace](https://huggingface.co/AtomicChat/Qwen-Image-2.1-Turbo-GGUF) \| [Mirror (CN)](https://hf-mirror.com/AtomicChat/Qwen-Image-2.1-Turbo-GGUF) |
| **Text Encoder** | `Qwen-Image-2.1-Turbo-Abliterated-Uncensored-AD-Q4_K.gguf` | `models/text_encoders/` | [HuggingFace](https://huggingface.co/AtomicChat/Qwen-Image-2.1-Turbo-Uncensored-GGUF) \| [Mirror (CN)](https://hf-mirror.com/AtomicChat/Qwen-Image-2.1-Turbo-Uncensored-GGUF) |
| **VAE** | `qwen_image_2.1_vae_bf16.safetensors` | `models/vae/` | [HuggingFace](https://huggingface.co/Qwen/Qwen-Image-2.1) \| [Mirror (CN)](https://hf-mirror.com/Qwen/Qwen-Image-2.1) |

#### 🔥 Preset 2: Qwen-Image-2.1-UC Uncensored INT8 (abenzerps Recommended)
*Pure native Safetensors format, uncensored DiT backbone with INT8 text encoder and BF16 VAE.*

| Component | File Name | Destination | Download Links |
| :--- | :--- | :--- | :--- |
| **Diffusion Model** | `qwen-image-2.1-UC-int8_convrot.safetensors` | `models/diffusion_models/` | [HuggingFace](https://huggingface.co/abenzerps/Qwen-Image-2.1-Uncensored-Quantized/tree/main) \| [Mirror (CN)](https://hf-mirror.com/abenzerps/Qwen-Image-2.1-Uncensored-Quantized) |
| **Text Encoder** | `qwen3vl_8b_int8_convrot.safetensors` | `models/text_encoders/` | [HuggingFace](https://huggingface.co/abenzerps/Qwen-Image-2.1-Uncensored-Quantized/tree/main) \| [Mirror (CN)](https://hf-mirror.com/abenzerps/Qwen-Image-2.1-Uncensored-Quantized) |
| **VAE** | `qwen_image_2.1_vae_bf16.safetensors` | `models/vae/` | [HuggingFace](https://huggingface.co/abenzerps/Qwen-Image-2.1-Uncensored-Quantized/tree/main) \| [Mirror (CN)](https://hf-mirror.com/abenzerps/Qwen-Image-2.1-Uncensored-Quantized) |

#### 🚀 Preset 3: Qwen-Image-2.1-Turbo 6-Step Dynamic (INT8 Safetensors)
*Powered by dynamic Viggle resolution-shifted schedule.*

| Component | File Name | Destination | Download Links |
| :--- | :--- | :--- | :--- |
| **Diffusion Model** | `Qwen-Image-2.1-viggle-turbo-v0.3-6step-int8_convrot.safetensors` | `models/diffusion_models/` | [HuggingFace](https://huggingface.co/Viggle/Qwen-Image-2.1-viggle-turbo) \| [Mirror (CN)](https://hf-mirror.com/Viggle/Qwen-Image-2.1-viggle-turbo) |
| **Text Encoder** | `qwen3vl_8b_int8_convrot.safetensors` | `models/text_encoders/` | [HuggingFace](https://huggingface.co/Comfy-Org/Qwen-Image-2.1) \| [Mirror (CN)](https://hf-mirror.com/Comfy-Org/Qwen-Image-2.1) |
| **VAE** | `qwen_image_2.1_vae_bf16.safetensors` | `models/vae/` | Same as Preset 1 |

#### 🎨 Preset 4: Z-Image Turbo Architecture (Single-Stream S3-DiT)
*Alibaba Tongyi-MAI's architecture, 8~9 steps Euler generation.*

| Component | File Name | Destination | Download Links |
| :--- | :--- | :--- | :--- |
| **Diffusion Model** | `z_image_turbo_int8_convrot.safetensors` | `models/diffusion_models/` | [HuggingFace](https://huggingface.co/Comfy-Org/z_image_turbo) \| [Mirror (CN)](https://hf-mirror.com/Comfy-Org/z_image_turbo) |
| **Text Encoder** | `qwen_3_4b_fp8_mixed_fixed.safetensors` (Fixed) or `qwen_3_4b.safetensors` | `models/text_encoders/` | [HuggingFace](https://huggingface.co/Comfy-Org/z_image_turbo) \| [Mirror (CN)](https://hf-mirror.com/Comfy-Org/z_image_turbo) |
| **VAE** | `ae.safetensors` (Flux VAE) | `models/vae/` | [HuggingFace](https://huggingface.co/Comfy-Org/z_image_turbo) \| [Mirror (CN)](https://hf-mirror.com/Comfy-Org/z_image_turbo) |

> 🛠️ **Z-Image Text Encoder Fix Guide (Fix-convert)**
> - **Why Fix-convert?**  
>   Standard community distributions of `qwen_3_4b_fp8_mixed.safetensors` contain 12 non-standard **NVFP4 2D block-quantized layers** (`.comfy_quant` and `weight_scale_2`). Native C++ engines (`stable-diffusion.cpp`) do not support these non-standard NVFP4 operators and will crash or output black images.  
>   The included `Fix-convert` utility uses GPU kernels to dequantize these 12 layers back to standard `bfloat16` while preserving standard FP8 layers, yielding the fully compatible `qwen_3_4b_fp8_mixed_fixed.safetensors`.
> - **How to use:**
>   1. Place `qwen_3_4b_fp8_mixed.safetensors` inside `Fix-convert/` (or drag and drop onto `一键修复.bat`);
>   2. Double-click `Fix-convert/一键修复.bat`;
>   3. The script outputs `qwen_3_4b_fp8_mixed_fixed.safetensors` in the same folder;
>   4. Copy the fixed file to `models/text_encoders/`.

#### ⚡ Preset 5: Krea-2 Turbo Architecture (Krea AI 12B DiT)
*Official open-source 12B aesthetic model, fast 8-step generation with Euler sampler and simple schedule.*

| Component | File Name | Destination | Download Links |
| :--- | :--- | :--- | :--- |
| **Diffusion Model** | `krea2_turbo_int8_convrot.safetensors` | `models/diffusion_models/` | [HuggingFace](https://huggingface.co/Comfy-Org/Krea-2) \| [Mirror (CN)](https://hf-mirror.com/Comfy-Org/Krea-2) |
| **Text Encoder** | `qwen3vl_4b_int8_convrot.safetensors` (Auto-aligned) | `models/text_encoders/` | [HuggingFace](https://huggingface.co/Comfy-Org/Krea-2) \| [Mirror (CN)](https://hf-mirror.com/Comfy-Org/Krea-2) |
| **VAE** | `qwen_image_vae.safetensors` | `models/vae/` | [HuggingFace](https://huggingface.co/Comfy-Org/Krea-2) \| [Mirror (CN)](https://hf-mirror.com/Comfy-Org/Krea-2) |

> 💡 **Qwen3-VL Automatic Compatibility**: Raw `qwen3vl_4b` text encoders downloaded from HuggingFace are automatically detected and converted to `_fixed` compatible weights upon first run—no manual conversion required.

---

## 🤖 Agent API (OpenAI Compatible)

Q-Spark features a high-performance HTTP endpoint compliant with the standard OpenAI DALL-E image generation protocol:

* **Endpoint**: `http://127.0.0.1:40188/v1/images/generations`
* **Method**: `POST`
* **Content-Type**: `application/json`

### Python Example

```python
import requests

url = "http://127.0.0.1:40188/v1/images/generations"
payload = {
    "prompt": "A cyberpunk kitten wearing neon holographic goggles, 8k masterpiece --ar 16:9",
    "size": "1360x768",
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

## 🧩 Universal AI Agent Skill Ecosystem (All-Agents Guide)

Q-Spark includes a standard image generation skill designed for **ANY AI Agent, coding assistant, or agent framework**:

* **Skill Directory**: [`skills/qspark/`](skills/qspark/) (contains `SKILL.md` capability manual & portable script `scripts/generate.py`)

### Why Use the Skill Pattern?
1. **Retain Reasoning LLM**: No need to swap your agent's reasoning model to an image generator; your agent continues using Claude 3.5 Sonnet, GPT-4o, or Gemini for high-level logic, calling Q-Spark only when artwork is needed.
2. **Single Source of Truth**: Active models and parameters dynamically follow `config.json` without hardcoded model strings.
3. **Zero Extra Dependencies**: `generate.py` is written in pure Python standard library, executable by any terminal-enabled agent in 1 second.
4. **Auto-Rendered Feedback**: Returns the local image path and clickable Markdown preview link `![image](file:///...)` directly into the chat stream.

---

### Integration Guide for Different Agent Types

#### 1. Terminal & Coding Agents (Claude Code, Cursor, Windsurf, Antigravity, Roo Code, Aider)
- **Direct CLI Invocation**: Instruct your agent to read [`skills/qspark/SKILL.md`](skills/qspark/SKILL.md). When generation is requested, the agent runs:
  ```powershell
  python "skills/qspark/scripts/generate.py" --prompt "cyberpunk cat, 8k resolution" --size "1360x768"
  ```
- **In-Chat Self-Installation**: Ask your agent in chat to install `skills/qspark` into its skill directory.
- **Global Installation (Machine-Wide across all projects)**:
  * **Windows**:
    ```powershell
    Copy-Item -Path "skills\qspark" -Destination "$env:USERPROFILE\.gemini\config\skills\qspark" -Recurse -Force
    ```
  * **Linux / macOS**:
    ```bash
    cp -r skills/qspark ~/.gemini/config/skills/qspark
    ```

#### 2. Python Agent Frameworks (LangChain, AutoGen, CrewAI, LlamaIndex)
Wrap `generate.py` as a native Tool / Function Call:
```python
import subprocess

def qspark_image_tool(prompt: str, size: str = "1024x1024") -> str:
    """Generate image via local Q-Spark engine and return file path."""
    cmd = ["python", "skills/qspark/scripts/generate.py", "--prompt", prompt, "--size", size]
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
```

#### 3. Platform & Workflow Agents (Dify, FastGPT, Coze, Cherry Studio, Chatbox)
For HTTP-driven agent platforms, configure via OpenAI-compatible API:
* **Protocol**: OpenAI Compatible
* **Base URL**: `http://127.0.0.1:40188/v1`
* **API Key**: `sk-any`
* **Endpoints**: `POST /v1/images/generations` or `POST /v1/chat/completions`

## 🛠️ Tech Stack & Acknowledgements

* **Inference Engine**: [stable-diffusion.cpp](https://github.com/leejet/stable-diffusion.cpp) (GGML C++ CUDA)
* **Foundational Models**: [Qwen-Image](https://github.com/QwenLM/Qwen-Image) & [Z-Image](https://huggingface.co/Tongyi-MAI/Z-Image-Turbo)
* **Frontend UI**: Native Vanilla HTML5 / CSS3 / JavaScript (zero heavy framework overhead)
* **API Framework**: [FastAPI](https://github.com/fastapi/fastapi) & [Uvicorn](https://github.com/encode/uvicorn)

---

## 📄 License

This project is licensed under the [Apache-2.0 License](LICENSE).
