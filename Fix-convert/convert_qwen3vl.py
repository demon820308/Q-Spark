import os
import sys
import safetensors
from safetensors.torch import save_file

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# 支持命令行传参/拖拽文件，未传参时默认读取同目录下的源模型
if len(sys.argv) > 1 and sys.argv[1].strip():
    SRC_PATH = sys.argv[1].strip('"')
    base_dir = os.path.dirname(SRC_PATH) or CURRENT_DIR
    stem = os.path.splitext(os.path.basename(SRC_PATH))[0]
    DST_PATH = os.path.join(base_dir, f"{stem}_fixed.safetensors")
else:
    SRC_PATH = os.path.join(CURRENT_DIR, "qwen3vl_4b_int8_convrot.safetensors")
    DST_PATH = os.path.join(CURRENT_DIR, "qwen3vl_4b_int8_fixed.safetensors")

def main():
    print(f"正在读取源文件: {SRC_PATH}")
    if not os.path.exists(SRC_PATH):
        print("错误: 未找到源文件！")
        print(f"请确认已将模型文件放置在同目录下: {SRC_PATH}")
        print("或者直接将 .safetensors 模型文件拖拽到 .bat 脚本上运行。")
        sys.exit(1)

    with safetensors.safe_open(SRC_PATH, framework="pt") as f:
        keys = list(f.keys())
        meta = f.metadata() or {}

        # 检查是否需要对齐
        has_lm_prefix = any(k.startswith("model.language_model.") for k in keys)
        if not has_lm_prefix:
            print("提示: 该模型不包含 model.language_model. 前缀，无需修复。")
            sys.exit(0)

        print(f"检测到 HuggingFace 原生多模态键名，正在对齐为 C++ 引擎与 ComfyUI 标准规范...")
        tensors = {}
        for k in keys:
            new_k = k
            if new_k.startswith("model.language_model."):
                new_k = "model." + new_k[len("model.language_model."):]
            elif new_k.startswith("model.visual."):
                new_k = "visual." + new_k[len("model.visual."):]
            elif new_k.startswith("lm_head."):
                new_k = "model.lm_head." + new_k[len("lm_head."):]
            tensors[new_k] = f.get_tensor(k)

    print(f"对齐完成，共处理 {len(tensors)} 个张量。")
    print(f"正在保存至: {DST_PATH}")
    save_file(tensors, DST_PATH, metadata=meta)
    print(f"恭喜! 兼容版模型已成功生成: {DST_PATH}")

if __name__ == "__main__":
    main()
