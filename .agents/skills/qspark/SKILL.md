---
name: qspark
description: >
  Generate images locally using the Q-Spark engine (stable-diffusion.cpp C++ backend).
  The active model and parameters are dynamically controlled by config.json (e.g. Z-Image,
  Qwen-Image, etc.). Use whenever the user asks to draw, paint, generate an image, or create
  artwork locally.
license: Apache-2.0
---

# Q-Spark Local Image Generation Skill

Use this skill to generate images via the local Q-Spark high-performance engine (`http://127.0.0.1:40188`).

## Dynamic Model Configuration

- **The image model is NOT fixed/hardcoded.** It dynamically follows the model configured in `config.json` (such as `z_image_turbo`, `Qwen-Image`, etc.).
- The agent should NOT assume a specific fixed model name. When image generation completes, the script outputs `MODEL_USED: <model_name>`, which the agent should report to the user.
- To inspect current configuration, run: `python "<skill_dir>/scripts/generate.py" --info`.

## Prerequisites

Q-Spark service must be running locally at `http://127.0.0.1:40188`.
If the service is not started, remind the user to run `start.bat` (or `Q-Spark.exe`) in the Q-Spark project root.

## Execution Procedure

Run the helper script via terminal/command execution tool:

```powershell
python "<skill_dir>/scripts/generate.py" --prompt "<prompt>" [--size "<width>x<height>"] [--steps <steps>]
```
*(Replace `<skill_dir>` with the path of this skill folder, e.g. `skills/qspark` in this repository or the installed skill directory).*

### Prompt & Parameter Guidelines

1. **Prompt Optimization**:
   - The active model natively supports both Chinese and English prompts.
   - For simple prompts, enrich them appropriately with quality descriptors (e.g. `8k resolution, high quality, detailed lighting, cinematic`).
2. **Aspect Ratio & Size Presets**:
   - `1:1` (Square): `1024x1024` (default)
   - `16:9` (Wide Landscape): `1360x768`
   - `9:16` (Mobile Portrait): `768x1360`
   - `4:3` (Standard Landscape): `1024x768`
   - `3:4` (Standard Portrait): `768x1024`
3. **Steps**:
   - By default, omit `--steps` so it automatically uses the recommended steps configured in `config.json` (e.g., 8 for Turbo models).
4. **Display Result**:
   - The script outputs the image path, markdown link, and `MODEL_USED: <model_name>`.
   - Embed the clickable markdown preview link `![Generated Image](file:///path/to/outputs/...)` and mention the active model used in the response.
