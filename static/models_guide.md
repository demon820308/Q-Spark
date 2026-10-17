### 📁 存放目录层级规范
请将下载好的模型文件放置到模型根目录（或 ComfyUI 的 `models` 目录）对应的子文件夹中：
- **`diffusion_models/`** ：降噪主模型（DiT / UNet 权重，如 `.safetensors` 或 `.gguf`）
- **`text_encoders/`**（或 `clip/`）：文本编码器（LLM / CLIP 权重）
- **`vae/`** ：变分自编码器（VAE 解码器权重）

---

### 🌟 套装一：Qwen-Image-2.1-Turbo GGUF 极速免审核版（8~10G 显存首选）
*专为 8~10G 显存优化，加载快、显存占用极低（仅需 4~6GB），支持 8 步快速出图且解除提示词审查。*

| 组件 | 文件名 | 存放子目录 | 下载页面 |  镜像直链 |
| :--- | :--- | :--- | :--- | :--- |
| **降噪主模型** | `Qwen-Image-2.1-Turbo-AD-Q4_K.gguf` | `diffusion_models/` | [HF官方](https://huggingface.co/AtomicChat/Qwen-Image-2.1-Turbo-GGUF) | [国内镜像](https://hf-mirror.com/AtomicChat/Qwen-Image-2.1-Turbo-GGUF) |
| **文本编码器** | `Qwen-Image-2.1-Turbo-Abliterated-Uncensored-AD-Q4_K.gguf` | `text_encoders/` | [HF官方](https://huggingface.co/AtomicChat/Qwen-Image-2.1-Turbo-Uncensored-GGUF) | [国内镜像](https://hf-mirror.com/AtomicChat/Qwen-Image-2.1-Turbo-Uncensored-GGUF) |
| **变分自编码器** | `qwen_image_2.1_vae_bf16.safetensors` | `vae/` | [HF官方](https://huggingface.co/Qwen/Qwen-Image-2.1) | [国内镜像](https://hf-mirror.com/Qwen/Qwen-Image-2.1) |

---

### 🔥 套装二：Qwen-Image-2.1-UC 免审核 INT8 完整量化套装（abenzerps 推荐）
*纯 Safetensors 原生量化格式，免审核（Uncensored）降噪核心，搭配 INT8 文本编码器与 BF16 VAE，画质与生成表现极其出色。*

| 组件 | 文件名 | 存放子目录 | 下载页面 |  镜像直链 |
| :--- | :--- | :--- | :--- | :--- |
| **降噪主模型** | `qwen-image-2.1-UC-int8_convrot.safetensors` | `diffusion_models/` | [HF官方](https://huggingface.co/abenzerps/Qwen-Image-2.1-Uncensored-Quantized/tree/main) | [国内镜像](https://hf-mirror.com/abenzerps/Qwen-Image-2.1-Uncensored-Quantized) |
| **文本编码器** | `qwen3vl_8b_int8_convrot.safetensors` | `text_encoders/` | [HF官方](https://huggingface.co/abenzerps/Qwen-Image-2.1-Uncensored-Quantized/tree/main) | [国内镜像](https://hf-mirror.com/abenzerps/Qwen-Image-2.1-Uncensored-Quantized) |
| **变分自编码器** | `qwen_image_2.1_vae_bf16.safetensors` | `vae/` | [HF官方](https://huggingface.co/abenzerps/Qwen-Image-2.1-Uncensored-Quantized/tree/main) | [国内镜像](https://hf-mirror.com/abenzerps/Qwen-Image-2.1-Uncensored-Quantized) |

---

### 🚀 套装三：Qwen-Image-2.1-Turbo 6步动态加速版（INT8 Safetensors）
*搭配 Viggle 动态调度算法，只需 6 步即可极速生成高质量图像。*

| 组件 | 文件名 | 存放子目录 | 下载页面 |  镜像直链 |
| :--- | :--- | :--- | :--- | :--- |
| **降噪主模型** | `Qwen-Image-2.1-viggle-turbo-v0.3-6step-int8_convrot.safetensors` | `diffusion_models/` | [HF官方](https://huggingface.co/Viggle/Qwen-Image-2.1-viggle-turbo) | [国内镜像](https://hf-mirror.com/Viggle/Qwen-Image-2.1-viggle-turbo) |
| **文本编码器** | `qwen3vl_8b_int8_convrot.safetensors` | `text_encoders/` | [HF官方](https://huggingface.co/Comfy-Org/Qwen-Image-2.1) | [国内镜像](https://hf-mirror.com/Comfy-Org/Qwen-Image-2.1) |
| **变分自编码器** | `qwen_image_2.1_vae_bf16.safetensors` | `vae/` | [HF官方](https://huggingface.co/Qwen/Qwen-Image-2.1) | [国内镜像](https://hf-mirror.com/Qwen/Qwen-Image-2.1) |

---

### 🎨 套装四：Z-Image Turbo 体系（阿里单流 S3-DiT 架构）
*阿里通义轻量开源架构，推荐步数 8~9 步，采样器 `euler`，调度器 `simple`。*

| 组件 | 文件名 | 存放子目录 | 下载页面 |  镜像直链 |
| :--- | :--- | :--- | :--- | :--- |
| **降噪主模型** | `z_image_turbo_int8_convrot.safetensors` | `diffusion_models/` | [HF官方](https://huggingface.co/Comfy-Org/z_image_turbo) | [国内镜像](https://hf-mirror.com/Comfy-Org/z_image_turbo) |
| **文本编码器** | `qwen_3_4b_fp8_mixed_fixed.safetensors` (修复版) 或 `qwen_3_4b.safetensors` | `text_encoders/` | [HF官方](https://huggingface.co/Comfy-Org/z_image_turbo) | [国内镜像](https://hf-mirror.com/Comfy-Org/z_image_turbo) |
| **变分自编码器** | `ae.safetensors` (Flux VAE) | `vae/` | [HF官方](https://huggingface.co/Comfy-Org/z_image_turbo) | [国内镜像](https://hf-mirror.com/Comfy-Org/z_image_turbo) |

#### ⚠️ Z-Image 文本编码器修复指南（Fix-convert 说明）
- **为什么要用 Fix-convert？**  
  社区和 Comfy-Org 常见的 `qwen_3_4b_fp8_mixed.safetensors` 中，有 12 个注意力层采用了**非标 NVFP4 2D 分块量化**（包含 `.comfy_quant` 和 `weight_scale_2`）。C++ 原生推理引擎（`sd-cpp`）不支持这种非标 NVFP4 格式，直接加载会导致报错崩溃或黑图。  
  通过项目内置的 `Fix-convert` 工具，可在 GPU 上将这 12 个非标层反量化还原为标准 `bfloat16`（其余标准 FP8 层原样保留），从而生成可被完美兼容调用的标准模型。
- **Fix-convert 使用步骤：**
  1. 将下载好的 `qwen_3_4b_fp8_mixed.safetensors` 放入项目中的 `Fix-convert/` 文件夹中（或直接将其鼠标拖拽到 `一键修复.bat` 上）；
  2. 双击运行 `Fix-convert/一键修复.bat`；
  3. 脚本会自动调用 ComfyUI 环境并在几秒内完成反量化，在同目录下生成 `qwen_3_4b_fp8_mixed_fixed.safetensors`；
  4. 将生成的修复版文件复制到 `models/text_encoders/` 目录中，在界面刷新选择即可。

---

### ⚡ 套装五：Krea-2 Turbo 体系（Krea AI 12B 单流 MMDiT 极速版）
*Krea AI 官方开源的 12B 级美学图像生成模型，支持 8 步蒸馏快速出图，推荐步数 8 步，采样器 `euler`，调度器 `simple`。*

| 组件 | 文件名 | 存放子目录 | 下载页面 | 镜像直链 |
| :--- | :--- | :--- | :--- | :--- |
| **降噪主模型 (INT8)** | `krea2_turbo_int8_convrot.safetensors` (推荐) | `diffusion_models/` | [HF官方](https://huggingface.co/Comfy-Org/Krea-2) | [国内镜像](https://modelscope.cn/models/Comfy-Org/Krea-2) |
| **降噪主模型 (FP8)** | `krea2_turbo_fp8_scaled.safetensors` | `diffusion_models/` | [HF官方](https://huggingface.co/Comfy-Org/Krea-2) | [国内镜像](https://modelscope.cn/models/Comfy-Org/Krea-2) |
| **文本编码器** | `qwen3vl_4b_int8_convrot.safetensors` (系统自动静默对齐) | `text_encoders/` | [HF官方](https://huggingface.co/Comfy-Org/Krea-2) | [国内镜像](https://modelscope.cn/models/Comfy-Org/Krea-2) |
| **变分自编码器** | `qwen_image_vae.safetensors` | `vae/` | [HF官方](https://huggingface.co/Comfy-Org/Krea-2) | [国内镜像](https://modelscope.cn/models/Comfy-Org/Krea-2) |

> 💡 **Qwen3-VL 自动适配说明**：原版从 HuggingFace / ModelScope 下载的 `qwen3vl_4b` 文本编码器，本项目引擎在首次点击生成时会自动毫秒级对齐键名并缓存为 `_fixed` 版本，无需手动做任何文件转换。

---

> 💡 **提示**：下载放置完成后，点击上方的 **「🔄 重新扫描模型」** 按钮，新模型即可立刻出现在下方下拉选择框中。
