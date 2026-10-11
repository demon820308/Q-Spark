### 📁 存放目录层级规范
请将下载好的模型文件放置到模型根目录（或 ComfyUI 的 `models` 目录）对应的子文件夹中：
- **`diffusion_models/`** ：降噪主模型（DiT / UNet 权重，如 `.safetensors` 或 `.gguf`）
- **`text_encoders/`**（或 `clip/`）：文本编码器（LLM / CLIP 权重）
- **`vae/`** ：变分自编码器（VAE 解码器权重）

---

### 🌟 事例一：Qwen-Image-2.1-Turbo GGUF 极速免审核套装（图示配置 / 显存极致优化）
*专为 8~10G 显存优化，加载快、显存占用极低（仅需 4~6GB），支持 8 步快速出图且解除提示词审查。*

| 组件 | 文件名 | 存放子目录 | 下载页面 / 镜像直链 |
| :--- | :--- | :--- | :--- |
| **降噪主模型** | `Qwen-Image-2.1-Turbo-AD-Q4_K.gguf` | `diffusion_models/` | [HF官方](https://huggingface.co/AtomicChat/Qwen-Image-2.1-Turbo-GGUF) \| [国内镜像](https://hf-mirror.com/AtomicChat/Qwen-Image-2.1-Turbo-GGUF) |
| **文本编码器** | `Qwen-Image-2.1-Turbo-Abliterated-Uncensored-AD-Q4_K.gguf` | `text_encoders/` | [HF官方](https://huggingface.co/AtomicChat/Qwen-Image-2.1-Turbo-Uncensored-GGUF) \| [国内镜像](https://hf-mirror.com/AtomicChat/Qwen-Image-2.1-Turbo-Uncensored-GGUF) |
| **变分自编码器** | `qwen_image_2.1_vae_bf16.safetensors` | `vae/` | [HF官方](https://huggingface.co/Qwen/Qwen-Image-2.1) \| [国内镜像](https://hf-mirror.com/Qwen/Qwen-Image-2.1) |

---

### 🚀 事例二：Qwen-Image-2.1-Turbo 6步动态加速版（INT8 Safetensors）
*搭配 Viggle 动态调度算法，只需 6 步即可极速生成高质量图像。*

| 组件 | 文件名 | 存放子目录 | 下载页面 / 镜像直链 |
| :--- | :--- | :--- | :--- |
| **降噪主模型** | `Qwen-Image-2.1-viggle-turbo-v0.3-6step-int8_convrot.safetensors` | `diffusion_models/` | [HF官方](https://huggingface.co/city96/Qwen-Image-2.1-Turbo-gguf) \| [国内镜像](https://hf-mirror.com/city96/Qwen-Image-2.1-Turbo-gguf) |
| **文本编码器** | `qwen3vl_8b_int8_convrot.safetensors` | `text_encoders/` | [HF官方](https://huggingface.co/city96/Qwen-Image-2.1-Turbo-gguf) \| [国内镜像](https://hf-mirror.com/city96/Qwen-Image-2.1-Turbo-gguf) |
| **变分自编码器** | `qwen_image_2.1_vae_bf16.safetensors` | `vae/` | 同上 |

---

### 🎨 事例三：Z-Image Turbo 体系（阿里最新轻量开源模型）
*全新架构单流 Diffusion Transformer，推荐步数 8~9 步，采样器 `euler`，调度器 `simple`。*

| 组件 | 文件名 | 存放子目录 | 下载页面 / 镜像直链 |
| :--- | :--- | :--- | :--- |
| **降噪主模型** | `z_image_turbo_int8_convrot.safetensors` | `diffusion_models/` | [HF官方](https://huggingface.co/Comfy-Org/z_image_turbo) \| [国内镜像](https://hf-mirror.com/Comfy-Org/z_image_turbo) |
| **文本编码器** | `qwen_3_4b_fixed.safetensors` 或 `qwen_3_4b.safetensors` | `text_encoders/` | [HF官方](https://huggingface.co/Comfy-Org/z_image_turbo) \| [国内镜像](https://hf-mirror.com/Comfy-Org/z_image_turbo) <br> *(⚠️ 注意：请勿使用带 NVFP4 2D分块量化的实验版)* |
| **变分自编码器** | `ae.safetensors` | `vae/` | [HF官方(Flux VAE)](https://huggingface.co/Comfy-Org/z_image_turbo) \| [国内镜像](https://hf-mirror.com/Comfy-Org/z_image_turbo) |

---
> 💡 **提示**：下载放置完成后，点击上方的 **「🔄 重新扫描模型」** 按钮，新模型即可立刻出现在下方下拉选择框中。
