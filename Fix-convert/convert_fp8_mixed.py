import os
import sys
import torch
import safetensors
from safetensors.torch import save_file
import comfy_kitchen as ck

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# 支持命令行传参/拖拽文件，未传参时默认读取同目录下的源模型
if len(sys.argv) > 1 and sys.argv[1].strip():
    SRC_PATH = sys.argv[1].strip('"')
    base_dir = os.path.dirname(SRC_PATH) or CURRENT_DIR
    stem = os.path.splitext(os.path.basename(SRC_PATH))[0]
    DST_PATH = os.path.join(base_dir, f"{stem}_fixed.safetensors")
else:
    SRC_PATH = os.path.join(CURRENT_DIR, "qwen_3_4b_fp8_mixed.safetensors")
    DST_PATH = os.path.join(CURRENT_DIR, "qwen_3_4b_fp8_mixed_fixed.safetensors")

def main():
    print(f"正在读取源文件: {SRC_PATH}")
    if not os.path.exists(SRC_PATH):
        print("错误: 未找到源文件！")
        print(f"请确认已将模型文件放置在同目录下: {SRC_PATH}")
        print("或者直接将 .safetensors 模型文件拖拽到 .bat 脚本上运行。")
        sys.exit(1)

    with safetensors.safe_open(SRC_PATH, framework="pt") as f:
        keys = list(f.keys())

        # 1. 扫描所有 NVFP4 量化的层
        nvfp4_bases = set()
        for k in keys:
            if k.endswith(".comfy_quant"):
                cq_bytes = bytes(f.get_tensor(k))
                cq_str = cq_bytes.decode("utf-8", errors="ignore")
                if "nvfp4" in cq_str:
                    base = k[:-len(".comfy_quant")]
                    nvfp4_bases.add(base)

        print(f"检测到 {len(nvfp4_bases)} 个 NVFP4 非标量化层需要反量化修复:")
        for b in sorted(nvfp4_bases):
            print(f"  - {b}")

        # 2. 准备输出字典
        output_tensors = {}
        processed_bases = set()

        for k in keys:
            # 检查当前张量是否属于 NVFP4 层
            matched_base = None
            for b in nvfp4_bases:
                if k == b or k.startswith(b + "."):
                    matched_base = b
                    break

            if matched_base:
                if matched_base not in processed_bases:
                    processed_bases.add(matched_base)
                    print(f"正在反量化 {matched_base} ...")
                    w = f.get_tensor(f"{matched_base}.weight")
                    ws = f.get_tensor(f"{matched_base}.weight_scale")
                    ws2 = f.get_tensor(f"{matched_base}.weight_scale_2")

                    # 使用 comfy_kitchen 官方 GPU 算子反量化为标准 bfloat16
                    w_bf16 = ck.dequantize_nvfp4(
                        w.cuda(),
                        ws2.cuda(),
                        ws.cuda(),
                        output_type=torch.bfloat16
                    ).cpu()

                    output_tensors[f"{matched_base}.weight"] = w_bf16
                    # 注意: weight_scale, weight_scale_2, comfy_quant 直接移除，不再写入
                continue

            # 对于标准层，直接复制
            output_tensors[k] = f.get_tensor(k)

    print(f"处理完成，共有 {len(output_tensors)} 个张量准备写入...")
    print(f"正在保存到: {DST_PATH}")
    save_file(output_tensors, DST_PATH)
    print(f"恭喜! 修复文件已成功生成: {DST_PATH}")

if __name__ == "__main__":
    main()
