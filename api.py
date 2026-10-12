import base64
import json
import os
import random
import re
import time
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict

from engine import (
    engine,
    APP_CONFIG,
    MODELS_DIR,
    OUTPUTS_DIR,
    OUTPUTS_JSON_DIR,
    BASE_DIR,
    DEFAULT_STEPS,
    save_config,
    scan_models,
    update_models_dir,
    get_system_metrics,
    get_api_model_status_text,
    to_rel_or_abs,
)

router = APIRouter()

ANSI_REGEX = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')

ASPECT_RATIO_PRESETS = {
    "1:1": (1024, 1024),
    "3:4": (768, 1024),
    "4:3": (1024, 768),
    "9:16": (768, 1360),
    "16:9": (1360, 768),
    "2:3": (832, 1248),
    "3:2": (1248, 832),
    "21:9": (1536, 640),
}


def _extract_from_text(text: Optional[str]) -> Optional[tuple[int, int]]:
    """从文本中提取尺寸或比例：支持 --ar 16:9、1792x1024、1024*1792、16:9、1:1 等"""
    if not text:
        return None
    s = text.strip()

    # 1. 优先提取显式 --ar X:Y 语法 (如 --ar 16:9, -ar 9:16, --ar 16/9, --ar 16：9)
    m_ar = re.search(r'--?ar\s+(\d+[:/：]\d+)', s, re.IGNORECASE)
    if m_ar:
        r = m_ar.group(1).replace("/", ":").replace("：", ":")
        if r in ASPECT_RATIO_PRESETS:
            return ASPECT_RATIO_PRESETS[r]

    # 2. 提取显式分辨率: 1792x1024, 1024*1792, 1024x1024, 1024*1024, 1792*1024 等
    m_dim = re.search(r'(?<!\d)(\d{3,4})\s*[\*xX×]\s*(\d{3,4})(?!\d)', s)
    if m_dim:
        try:
            w = int(m_dim.group(1))
            h = int(m_dim.group(2))
            w = max(256, min(2048, round(w / 16) * 16))
            h = max(256, min(2048, round(h / 16) * 16))
            return w, h
        except Exception:
            pass

    # 3. 提取独立比例预设: 1:1, 16:9, 9:16, 4:3, 3:4, 2:3, 3:2, 21:9 等
    for m_ratio in re.finditer(r'(?<!\d)(\d{1,2})\s*[:/：]\s*(\d{1,2})(?!\d)', s):
        ratio_key = f"{m_ratio.group(1)}:{m_ratio.group(2)}"
        if ratio_key in ASPECT_RATIO_PRESETS:
            return ASPECT_RATIO_PRESETS[ratio_key]

    return None


def resolve_dimensions(size_str: Optional[str] = None, prompt_str: str = "") -> tuple[int, int]:
    """智能解析尺寸与比例：支持分辨率 (1792x1024 / 1024*1792)、比例 (16:9, 9:16, 1:1, 4:3, 3:4) 以及 --ar 16:9"""
    dim_from_prompt = _extract_from_text(prompt_str)
    if dim_from_prompt:
        return dim_from_prompt

    if size_str:
        dim_from_size = _extract_from_text(size_str)
        if dim_from_size:
            return dim_from_size

    return 1024, 1024


# ==============================================================================
# Pydantic 请求模型
# ==============================================================================
class OpenAIGenRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    prompt: str
    size: Optional[str] = "1024x1024"
    n: Optional[int] = 1
    response_format: Optional[str] = "url"
    steps: Optional[int] = DEFAULT_STEPS


class OpenAIChatRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    model: Optional[str] = "qwen-image-2.1-turbo"
    messages: list[dict]
    stream: Optional[bool] = False


class UIGenerateRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    prompt: str
    width: Optional[int] = 1024
    height: Optional[int] = 1024
    steps: Optional[int] = 8
    seed: Optional[int] = -1
    policy: Optional[str] = "on_demand"
    diff_model: Optional[str] = None
    te_model: Optional[str] = None
    vae_model: Optional[str] = None
    negative_prompt: Optional[str] = ""
    cfg_scale: Optional[float] = 1.0
    loras: Optional[list] = None
    init_image: Optional[str] = None
    ref_images: Optional[list] = None
    mode: Optional[str] = "txt2img"


class UISaveConfigRequest(BaseModel):
    diff_model: Optional[str] = None
    te_model: Optional[str] = None
    vae_model: Optional[str] = None
    steps: Optional[int] = 8
    policy: Optional[str] = None


class UIScanModelsRequest(BaseModel):
    models_dir: Optional[str] = None


class UIDeletePresetRequest(BaseModel):
    models_dir: str


# ==============================================================================
# 1. 显存与硬件监控 API
# ==============================================================================
@router.get("/api/vram/status")
async def get_vram_status():
    return {"status": engine.get_status_text(), "mode": engine.mode}


@router.post("/api/vram/flush")
async def flush_vram_api():
    msg = engine.stop_server()
    return {"message": msg, "status": engine.get_status_text()}


@router.post("/api/task/stop")
async def stop_task_api():
    msg = engine.stop_task()
    return {"message": msg, "stopped": True}


@router.get("/api/metrics")
async def get_metrics_api():
    return get_system_metrics()


# ==============================================================================
# 2. UI 配置管理与模型扫描 API
# ==============================================================================
@router.get("/api/config")
async def get_ui_config():
    diff_choices, te_choices, vae_choices, lora_choices = scan_models()
    return {
        "config": APP_CONFIG,
        "models_dir": to_rel_or_abs(MODELS_DIR),
        "models_dir_history": APP_CONFIG.get("models_dir_history", [to_rel_or_abs(MODELS_DIR)]),
        "diff_choices": diff_choices,
        "te_choices": te_choices,
        "vae_choices": vae_choices,
        "lora_choices": lora_choices,
        "status_text": engine.get_status_text(),
        "api_status_text": get_api_model_status_text(),
        "engine_mode": engine.mode,
    }


@router.post("/api/config")
async def save_ui_config(req: UISaveConfigRequest):
    if req.diff_model:
        APP_CONFIG["api_diff_model"] = req.diff_model
    if req.te_model:
        APP_CONFIG["api_te_model"] = req.te_model
    if req.vae_model:
        APP_CONFIG["api_vae_model"] = req.vae_model
    if req.steps and req.steps > 0:
        APP_CONFIG["api_steps"] = req.steps
    if req.policy:
        engine.mode = req.policy

    save_config(APP_CONFIG)
    return {
        "success": True,
        "message": f"已成功持久化至 config.json，外部 Agent 将默认调用 `{APP_CONFIG.get('api_diff_model')}`",
        "api_status_text": get_api_model_status_text(),
    }


@router.post("/api/models/scan")
async def scan_models_api(req: UIScanModelsRequest):
    p_str = req.models_dir.strip() if req.models_dir else ""
    if p_str:
        p = Path(p_str)
        if not p.is_absolute():
            p = (BASE_DIR / p).resolve()
    else:
        p = (BASE_DIR / "models").resolve()

    if not p.exists() or not p.is_dir():
        raise HTTPException(status_code=400, detail=f"路径不存在或不是有效文件夹: {p}")

    update_models_dir(p)
    rel_p = to_rel_or_abs(p)
    APP_CONFIG["models_dir"] = rel_p

    hist = APP_CONFIG.setdefault("models_dir_history", [])
    if rel_p not in hist:
        hist.insert(0, rel_p)
    save_config(APP_CONFIG)

    diff_choices, te_choices, vae_choices, lora_choices = scan_models(p)
    return {
        "success": True,
        "models_dir": rel_p,
        "models_dir_history": hist,
        "diff_choices": diff_choices,
        "te_choices": te_choices,
        "vae_choices": vae_choices,
        "lora_choices": lora_choices,
        "message": f"模型目录已更新并扫描：主模型 {len(diff_choices)} 个 | 文本编码器 {len(te_choices)} 个 | VAE {len(vae_choices)} 个 | LoRA {len(lora_choices)} 个",
    }


@router.post("/api/models/preset/delete")
async def delete_preset_api(req: UIDeletePresetRequest):
    target = req.models_dir.strip()
    hist = APP_CONFIG.setdefault("models_dir_history", [to_rel_or_abs(MODELS_DIR)])
    if target in hist:
        hist.remove(target)
    if not hist:
        hist = ["models"]
    APP_CONFIG["models_dir_history"] = hist

    if APP_CONFIG.get("models_dir") == target:
        APP_CONFIG["models_dir"] = hist[0]
        p = Path(hist[0])
        if not p.is_absolute():
            p = (BASE_DIR / p).resolve()
        update_models_dir(p)

    save_config(APP_CONFIG)
    diff_choices, te_choices, vae_choices, lora_choices = scan_models()
    return {
        "success": True,
        "models_dir": APP_CONFIG.get("models_dir"),
        "models_dir_history": hist,
        "diff_choices": diff_choices,
        "te_choices": te_choices,
        "vae_choices": vae_choices,
        "lora_choices": lora_choices,
        "message": f"已从预设列表中删除目录：{target}",
    }


@router.get("/api/docs/models")
async def get_models_doc():
    doc_path = BASE_DIR / "static" / "models_guide.md"
    if doc_path.exists():
        return {"content": doc_path.read_text(encoding="utf-8")}
    return {"content": "暂无说明文档"}


# ==============================================================================
# 3. 前端 UI SSE 实时生图 API
# ==============================================================================
@router.post("/api/generate")
async def ui_generate(req: UIGenerateRequest):
    if not req.prompt or not req.prompt.strip():
        raise HTTPException(status_code=400, detail="提示词不能为空")

    if req.policy:
        engine.mode = req.policy

    async def sse_generator():
        start_t = time.time()
        try:
            async for ev in engine.generate_image_stream(
                prompt=req.prompt.strip(),
                width=req.width or 1024,
                height=req.height or 1024,
                steps=req.steps,
                seed=req.seed if req.seed is not None else -1,
                diff_model=req.diff_model or "",
                te_model=req.te_model or "",
                vae_model=req.vae_model or "",
                negative_prompt=req.negative_prompt or "",
                cfg_scale=req.cfg_scale or 1.0,
                loras=req.loras or [],
                source="web",
                init_image=req.init_image,
                ref_images=req.ref_images,
                mode=req.mode,
            ):
                payload = {
                    "pct": ev.get("pct", 0.0),
                    "desc": ev.get("desc", ""),
                }
                log_chunk = ev.get("log", "")
                if log_chunk:
                    cleaned = ANSI_REGEX.sub("", log_chunk)
                    payload["log"] = cleaned

                if "out_path" in ev:
                    out_path = ev["out_path"]
                    filename = os.path.basename(out_path)
                    payload["image_url"] = f"/outputs/{filename}"
                    payload["out_path"] = out_path
                    payload["diff_model"] = ev.get("diff_model", "")
                    payload["cost"] = round(time.time() - start_t, 2)

                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")


# ==============================================================================
# 4. OpenAI 兼容协议 (Agent 接入专用)
# ==============================================================================
@router.get("/v1/models")
@router.get("/models")
async def openai_get_models():
    """返回符合 OpenAI 规范的模型列表，供 Agent 客户端（如 Cherry Studio）一键自动导入模型"""
    model_ids = ["qwen-image-2.1-turbo", "dall-e-3"]
    return {
        "object": "list",
        "data": [
            {
                "id": m_id,
                "object": "model",
                "created": 1700000000,
                "owned_by": "local",
                "permission": [],
                "root": m_id,
                "parent": None,
            }
            for m_id in model_ids
        ],
    }


@router.post("/v1/images/generations")
@router.post("/images/generations")
async def openai_images_generations(req: OpenAIGenRequest):
    w, h = resolve_dimensions(req.size, req.prompt)

    start_t = time.time()
    out_path = None
    actual_diff_model = APP_CONFIG.get("api_diff_model", "")
    try:
        async for event in engine.generate_image_stream(
            prompt=req.prompt, width=w, height=h, steps=req.steps, source="api_dalle"
        ):
            if "out_path" in event:
                out_path = event["out_path"]
            if "diff_model" in event:
                actual_diff_model = event["diff_model"]
        if not out_path:
            raise RuntimeError("生图流程未产出有效图片路径。")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    filename = os.path.basename(out_path)
    url_link = f"http://127.0.0.1:40188/outputs/{filename}"

    with open(out_path, "rb") as f:
        b64_data = base64.b64encode(f.read()).decode("utf-8")

    return {
        "created": int(start_t),
        "data": [
            {
                "url": url_link,
                "b64_json": b64_data,
                "revised_prompt": f"Model: {actual_diff_model}",
            }
        ],
    }


@router.post("/v1/chat/completions")
@router.post("/chat/completions")
async def openai_chat_completions(req: OpenAIChatRequest):
    """兼容对话补全协议 (openai-completions)，允许在 Agent 对话框内直接出图"""
    prompt = ""
    for msg in reversed(req.messages):
        if msg.get("role") == "user":
            content = msg.get("content", "")
            if isinstance(content, str):
                prompt = content.strip()
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        prompt = part.get("text", "").strip()
            if prompt:
                break

    if not prompt:
        prompt = "a beautiful landscape"

    w, h = resolve_dimensions(prompt_str=prompt)
    steps = None
    m_steps = re.search(r'--?steps?\s+(\d+)', prompt, re.IGNORECASE)
    if m_steps:
        try:
            steps = int(m_steps.group(1))
        except Exception:
            pass

    created_t = int(time.time())
    chat_id = f"chatcmpl-{created_t}-{random.randint(1000, 9999)}"
    model_name = req.model or "qwen-image-2.1-turbo"

    if req.stream:
        async def chat_stream_generator():
            out_path = None
            last_reported_desc = ""
            actual_diff_model = APP_CONFIG.get("api_diff_model", "")
            start_t = time.time()
            try:
                # 1. 发送助手角色与思考块开头
                step_hint = f" | 步数: {steps}" if steps else ""
                init_chunks = [
                    {"role": "assistant"},
                    {"content": "<think>\n"},
                    {"content": f"> 🚀 硬件平台: 本地 NVIDIA GPU | 生图规格: {w}x{h}{step_hint}\n"},
                ]
                for c in init_chunks:
                    chunk = {
                        "id": chat_id,
                        "object": "chat.completion.chunk",
                        "created": created_t,
                        "model": model_name,
                        "choices": [{"index": 0, "delta": c, "finish_reason": None}],
                    }
                    yield f"data: {json.dumps(chunk)}\n\n"

                # 2. 监听流式推理事件，实时向 Agent 对话框推送阶段进度
                async for event in engine.generate_image_stream(prompt=prompt, width=w, height=h, steps=steps, source="api_chat"):
                    desc = event.get("desc", "")
                    if desc and desc != last_reported_desc:
                        if "397" in desc or "265" in desc:
                            if not last_reported_desc.startswith("正在加载模型"):
                                desc_line = "> ⚙️ 正在载入多模态模型权重...\n"
                                last_reported_desc = "正在加载模型"
                            else:
                                continue
                        else:
                            last_reported_desc = desc
                            desc_line = f"> ⏳ {desc}\n"

                        chunk = {
                            "id": chat_id,
                            "object": "chat.completion.chunk",
                            "created": created_t,
                            "model": model_name,
                            "choices": [{"index": 0, "delta": {"content": desc_line}, "finish_reason": None}],
                        }
                        yield f"data: {json.dumps(chunk)}\n\n"

                    if "out_path" in event:
                        out_path = event["out_path"]
                    if "diff_model" in event:
                        actual_diff_model = event["diff_model"]

                cost = time.time() - start_t
                # 3. 闭合思考标签
                close_think_chunk = {
                    "id": chat_id,
                    "object": "chat.completion.chunk",
                    "created": created_t,
                    "model": model_name,
                    "choices": [{"index": 0, "delta": {"content": f"> ✨ 推理生成完成，耗时 {cost:.1f}s\n</think>\n\n"}, "finish_reason": None}],
                }
                yield f"data: {json.dumps(close_think_chunk)}\n\n"

                # 4. 推送最终高清图像 Markdown
                if out_path:
                    filename = os.path.basename(out_path)
                    url_link = f"http://127.0.0.1:40188/outputs/{filename}"
                    model_display = f" ｜ 🧩 当前主模型: `{actual_diff_model}`" if actual_diff_model else ""
                    content_str = f"![image]({url_link})\n\n[🔍 点击查看高清原图]({url_link}){model_display}"
                else:
                    content_str = "❌ 图像生成未产出有效文件。"

                content_chunk = {
                    "id": chat_id,
                    "object": "chat.completion.chunk",
                    "created": created_t,
                    "model": model_name,
                    "choices": [{"index": 0, "delta": {"content": content_str}, "finish_reason": None}],
                }
                yield f"data: {json.dumps(content_chunk)}\n\n"

            except Exception as e:
                err_chunk = {
                    "id": chat_id,
                    "object": "chat.completion.chunk",
                    "created": created_t,
                    "model": model_name,
                    "choices": [{"index": 0, "delta": {"content": f"\n</think>\n\n❌ 生成出错: {str(e)}"}, "finish_reason": None}],
                }
                yield f"data: {json.dumps(err_chunk)}\n\n"

            stop_chunk = {
                "id": chat_id,
                "object": "chat.completion.chunk",
                "created": created_t,
                "model": model_name,
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
            }
            yield f"data: {json.dumps(stop_chunk)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(chat_stream_generator(), media_type="text/event-stream")

    out_path = None
    actual_diff_model = APP_CONFIG.get("api_diff_model", "")
    try:
        async for event in engine.generate_image_stream(prompt=prompt, width=w, height=h, steps=steps, source="api_chat"):
            if "out_path" in event:
                out_path = event["out_path"]
            if "diff_model" in event:
                actual_diff_model = event["diff_model"]
        if not out_path:
            raise RuntimeError("生图流程未产出有效图片路径。")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    filename = os.path.basename(out_path)
    url_link = f"http://127.0.0.1:40188/outputs/{filename}"
    model_display = f" ｜ 🧩 当前主模型: `{actual_diff_model}`" if actual_diff_model else ""
    reply_content = f"![image]({url_link})\n\n[🔍 点击查看高清原图]({url_link}){model_display}"

    return {
        "id": chat_id,
        "object": "chat.completion",
        "created": created_t,
        "model": model_name,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": reply_content,
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": len(prompt),
            "completion_tokens": len(reply_content),
            "total_tokens": len(prompt) + len(reply_content),
        },
    }


# ==============================================================================
# 5. 历史画廊管理 API
# ==============================================================================
@router.get("/api/history")
async def get_history_api(page: int = 1, page_size: int = 24, source: Optional[str] = None):
    """获取历史画廊元数据列表，按生成时间倒序分页"""
    if not OUTPUTS_JSON_DIR.exists():
        return {"total": 0, "page": page, "page_size": page_size, "items": []}

    records = []
    for jf in OUTPUTS_JSON_DIR.glob("*.json"):
        try:
            with open(jf, "r", encoding="utf-8") as f:
                data = json.load(f)
            fn = data.get("filename", f"{jf.stem}.png")
            img_path = OUTPUTS_DIR / fn
            # 校验对应图片文件是否存在，不存在则跳过（避免孤立残存记录）
            if not img_path.exists():
                continue
            data["image_url"] = f"/outputs/{fn}"
            if source and source != "all" and data.get("source") != source:
                continue
            records.append(data)
        except Exception:
            continue

    # 按 created_at 倒序排列
    records.sort(key=lambda x: x.get("created_at", 0), reverse=True)

    total = len(records)
    start_idx = max(0, (page - 1) * page_size)
    end_idx = start_idx + page_size
    items = records[start_idx:end_idx]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items,
    }


@router.delete("/api/history/{filename}")
async def delete_history_api(filename: str):
    """删除指定的历史记录及其关联图片与 JSON 文件"""
    safe_name = os.path.basename(filename)
    stem = Path(safe_name).stem
    img_path = OUTPUTS_DIR / safe_name
    json_path = OUTPUTS_JSON_DIR / f"{stem}.json"

    deleted_img = False
    deleted_json = False

    if img_path.exists():
        try:
            img_path.unlink()
            deleted_img = True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"删除图片文件失败: {e}")

    if json_path.exists():
        try:
            json_path.unlink()
            deleted_json = True
        except Exception:
            pass

    return {
        "success": True,
        "filename": safe_name,
        "deleted_img": deleted_img,
        "deleted_json": deleted_json,
    }
