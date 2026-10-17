# 模型兼容性修复工具箱 (Fix-convert)

本工具箱提供针对非标 safetensors 模型的兼容性修复工具：
1. **NVFP4 非标量化还原**：修复 Z-Image 的 `qwen_3_4b_fp8_mixed.safetensors`；
2. **Qwen3-VL 键名规范对齐**：对齐 HuggingFace 原生 `qwen3vl_4b/8b` 文本编码器规范。

---

## 🛠️ 工具一：Z-Image Qwen 3 4B FP8 Mixed 非标 NVFP4 修复


### 问题背景
原始模型中的部分网络层使用了 **NVFP4 2D 分块非标量化**（带有 `.comfy_quant` 与 `weight_scale_2`）。这会导致在很多标准推理框架或旧版环境中加载报错、识别异常或无法直接使用。

### 修复原理
本脚本借助 `comfy_kitchen` 的 GPU 反量化算子：
1. 自动扫描模型中所有被标记为 `nvfp4` 的量化层；
2. 在 CUDA 设备上将 NVFP4 权重精确还原为标准的 `bfloat16` 格式；
3. 自动剔除量化专用的 `weight_scale`、`weight_scale_2` 和 `comfy_quant` 键；
4. 其余正常标准层原样保持不变；
5. 生成完全符合通用标准的 `qwen_3_4b_fp8_mixed_fixed.safetensors`。

---

### 使用方法

#### 方式一：放在同一目录下双击运行（推荐）
1. 将待修复的 `qwen_3_4b_fp8_mixed.safetensors` 复制到本文件夹（`Fix-convert`）内；
2. 双击运行 `一键修复.bat`；
3. 等待命令行执行完毕，同目录下会生成 `qwen_3_4b_fp8_mixed_fixed.safetensors`；
4. 将生成的修复版模型放回您的 ComfyUI 或模型对应目录使用即可。

#### 方式二：拖拽模型文件修复
- 直接把任意位置的 `qwen_3_4b_fp8_mixed.safetensors` 鼠标拖拽并松手投放到 `一键修复.bat` 上，脚本会自动在源模型所在目录生成对应的 `_fixed.safetensors` 文件。

---

### 环境与硬件要求
- **显卡**：NVIDIA GPU（反量化过程需调用 CUDA）。
- **Python 环境**：需要安装有 `torch`、`safetensors` 以及 `comfy_kitchen`。
  - 脚本默认会自动匹配检测 ComfyUI 的内置 Python 环境（`python_embeded`）。

---

## 🛠️ 工具二：Qwen3-VL 文本编码器 HuggingFace 键名规范对齐 (`convert_qwen3vl.py` / `一键修复_Qwen3VL.bat`)

### 问题背景
从 HuggingFace / ModelScope 下载的原生 `qwen3vl_4b_int8_convrot.safetensors` 等文本编码器，其权重包含原生 `model.language_model.` 前缀。纯 C++ 推理引擎（`stable-diffusion.cpp`）期望以 `model.` 开头的标准键名，直接加载会导致张量元数据校验失败。

> 💡 **自动适配提示**：在 Q-Spark v0.2.7 及更高版本中，服务在生图前会自动检测并毫秒级静默生成 `_fixed.safetensors`，无需任何手动操作。本离线工具专为需要预先处理、批量分发或在第三方环境运行的用户提供。

### 使用方法
- **拖拽修复**：直接将任意 `qwen3vl_*.safetensors` 模型拖拽投放到 `一键修复_Qwen3VL.bat` 上，脚本将在同目录自动生成对齐后的 `*_fixed.safetensors` 文件；
- **命令行调用**：
  ```bash
  python convert_qwen3vl.py path/to/qwen3vl_4b_int8_convrot.safetensors
  ```
