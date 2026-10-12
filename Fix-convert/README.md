# Z-Image Qwen 3 4B FP8 Mixed 模型修复工具

本工具专门针对 **z-image** 的 `qwen_3_4b_fp8_mixed.safetensors` 文本编码器模型进行修复。

---

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
