import os
import sys
import shutil
import urllib.request
import json
import zipfile
import subprocess
import argparse

def log(msg: str):
    print(f"[Build] {msg}", flush=True)

def download_file(url: str, dest_path: str):
    log(f"Downloading: {url} -> {dest_path}")
    headers = {"User-Agent": "Q-Spark-Builder"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response, open(dest_path, "wb") as out_file:
        total = int(response.headers.get("content-length", 0))
        downloaded = 0
        chunk_size = 1024 * 1024  # 1MB
        while True:
            chunk = response.read(chunk_size)
            if not chunk:
                break
            out_file.write(chunk)
            downloaded += len(chunk)
            if total > 0:
                percent = downloaded * 100 // total
                if downloaded % (10 * 1024 * 1024) < chunk_size or downloaded == total:
                    print(f"\r  Downloaded: {downloaded / (1024*1024):.1f}/{total / (1024*1024):.1f} MB ({percent}%)", end="", flush=True)
        print()

def ensure_bin(bin_dir: str):
    sd_cli = os.path.join(bin_dir, "sd-cli.exe")
    if os.path.exists(sd_cli):
        log(f"bin directory already present: {bin_dir}")
        return

    os.makedirs(bin_dir, exist_ok=True)
    log("Fetching latest stable-diffusion.cpp release info...")
    req = urllib.request.Request("https://api.github.com/repos/leejet/stable-diffusion.cpp/releases/latest", headers={"User-Agent": "Q-Spark-Builder"})
    with urllib.request.urlopen(req) as resp:
        rel_data = json.loads(resp.read().decode())

    cuda_zip_url = None
    cudart_zip_url = None
    for asset in rel_data.get("assets", []):
        name = asset["name"].lower()
        if "bin-win-cuda12-x64" in name:
            cuda_zip_url = asset["browser_download_url"]
        elif "cudart-sd-bin-win-cu12-x64" in name:
            cudart_zip_url = asset["browser_download_url"]

    if not cuda_zip_url or not cudart_zip_url:
        raise RuntimeError("Failed to find CUDA 12 assets in stable-diffusion.cpp release!")

    temp_dir = os.path.join(bin_dir, "_temp")
    os.makedirs(temp_dir, exist_ok=True)

    cuda_zip = os.path.join(temp_dir, "sd-cuda.zip")
    cudart_zip = os.path.join(temp_dir, "cudart.zip")

    download_file(cuda_zip_url, cuda_zip)
    log("Extracting sd-cuda.zip...")
    with zipfile.ZipFile(cuda_zip, "r") as z:
        for member in z.infolist():
            # Flatten or extract bin files
            fn = os.path.basename(member.filename)
            if fn and not member.is_dir():
                target = os.path.join(bin_dir, fn)
                with z.open(member) as source, open(target, "wb") as dest:
                    shutil.copyfileobj(source, dest)

    download_file(cudart_zip_url, cudart_zip)
    log("Extracting cudart.zip...")
    with zipfile.ZipFile(cudart_zip, "r") as z:
        for member in z.infolist():
            fn = os.path.basename(member.filename)
            if fn and not member.is_dir():
                target = os.path.join(bin_dir, fn)
                with z.open(member) as source, open(target, "wb") as dest:
                    shutil.copyfileobj(source, dest)

    shutil.rmtree(temp_dir, ignore_errors=True)
    log("Binary dependencies setup complete.")

def ensure_python_embeded(py_dir: str, root_dir: str):
    py_exe = os.path.join(py_dir, "python.exe")
    site_packages = os.path.join(py_dir, "Lib", "site-packages")
    if os.path.exists(py_exe) and os.path.exists(os.path.join(site_packages, "gradio")):
        log(f"python_embeded already present: {py_dir}")
        return

    os.makedirs(py_dir, exist_ok=True)
    py_zip_url = "https://www.python.org/ftp/python/3.12.9/python-3.12.9-embed-amd64.zip"
    temp_zip = os.path.join(py_dir, "python-embed.zip")
    download_file(py_zip_url, temp_zip)

    log("Extracting Python embed package...")
    with zipfile.ZipFile(temp_zip, "r") as z:
        z.extractall(py_dir)
    if os.path.exists(temp_zip):
        os.remove(temp_zip)

    # Configure python312._pth to enable site-packages
    pth_file = os.path.join(py_dir, "python312._pth")
    if os.path.exists(pth_file):
        with open(pth_file, "r", encoding="utf-8") as f:
            content = f.read()
        lines = content.splitlines()
        new_lines = []
        for line in lines:
            if line.strip() == "#import site":
                new_lines.append("import site")
            else:
                new_lines.append(line)
        new_lines.append(".")
        new_lines.append("..")
        new_lines.append(r"Lib\site-packages")
        with open(pth_file, "w", encoding="utf-8") as f:
            f.write("\n".join(new_lines) + "\n")
        log("Configured python312._pth")

    os.makedirs(site_packages, exist_ok=True)
    req_file = os.path.join(root_dir, "requirements.txt")
    log("Installing dependencies into python_embeded site-packages...")
    cmd = [
        sys.executable, "-m", "pip", "install",
        "-r", req_file,
        "--target", site_packages,
        "--no-warn-script-location"
    ]
    subprocess.check_call(cmd)
    log("Python embed dependencies installed successfully.")

def compile_launcher(root_dir: str, output_exe: str):
    cs_file = os.path.join(root_dir, "Q-Spark.cs")
    ico_file = os.path.join(root_dir, "app.ico")
    if not os.path.exists(cs_file):
        log(f"Q-Spark.cs not found at {cs_file}, skipping launcher compile")
        return

    csc_candidates = [
        r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe",
        r"C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe",
        "csc.exe"
    ]
    csc_exe = None
    for cand in csc_candidates:
        if os.path.exists(cand) or shutil.which(cand):
            csc_exe = cand
            break

    if not csc_exe:
        log("Warning: csc compiler not found. Skipping Q-Spark.exe compilation.")
        return

    log(f"Compiling launcher {output_exe} with {csc_exe}...")
    cmd = [
        csc_exe,
        "/target:winexe",
        f"/win32icon:{ico_file}",
        f"/out:{output_exe}",
        cs_file
    ]
    subprocess.check_call(cmd)
    log("Compiled Q-Spark.exe successfully.")

def build_portable(version: str, output_dir: str):
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_name = f"Q-Spark-{version}-windows-x64-portable"
    build_dir = os.path.join(root_dir, "build_portable_staging", target_name)
    os.makedirs(build_dir, exist_ok=True)

    log(f"=== Starting Build for {target_name} ===")

    # 1. Binaries (sd-cli + CUDA DLLs)
    local_bin = os.path.join(root_dir, "bin")
    staging_bin = os.path.join(build_dir, "bin")
    if os.path.exists(os.path.join(local_bin, "sd-cli.exe")):
        log("Copying existing local bin directory...")
        shutil.copytree(local_bin, staging_bin, dirs_exist_ok=True)
    else:
        ensure_bin(staging_bin)

    # 2. Python Embedded
    local_py = os.path.join(root_dir, "python_embeded")
    staging_py = os.path.join(build_dir, "python_embeded")
    if os.path.exists(os.path.join(local_py, "python.exe")):
        log("Copying existing local python_embeded directory...")
        shutil.copytree(local_py, staging_py, dirs_exist_ok=True)
    else:
        ensure_python_embeded(staging_py, root_dir)

    # 3. Compile Launcher
    launcher_exe = os.path.join(build_dir, "Q-Spark.exe")
    compile_launcher(root_dir, launcher_exe)

    # 4. Copy Core Files
    for fn in ["app.py", "config.json", "start.bat", "app.ico", "README.md", "README_zh.md", "LICENSE"]:
        src = os.path.join(root_dir, fn)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(build_dir, fn))
            log(f"Copied {fn}")

    # 5. Create empty directories
    for sub in ["models/diffusion_models", "models/text_encoders", "models/vae", "outputs"]:
        d = os.path.join(build_dir, sub)
        os.makedirs(d, exist_ok=True)
        # Place empty marker
        with open(os.path.join(d, ".keep"), "w", encoding="utf-8") as f:
            f.write("")

    # 6. Package into ZIP
    final_zip = os.path.join(output_dir, f"{target_name}.zip")
    log(f"Creating portable zip archive: {final_zip} ...")
    
    with zipfile.ZipFile(final_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for root, dirs, files in os.walk(build_dir):
            for file in files:
                abs_f = os.path.join(root, file)
                rel_f = os.path.relpath(abs_f, os.path.dirname(build_dir))
                z.write(abs_f, rel_f)

    # Cleanup staging
    shutil.rmtree(os.path.dirname(build_dir), ignore_errors=True)
    sz_mb = os.path.getsize(final_zip) / (1024 * 1024)
    log(f"Build completed successfully! Package: {final_zip} ({sz_mb:.2f} MB)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="0.1.0", help="Release version (default: 0.1.0)")
    parser.add_argument("--output-dir", default=None, help="Output directory for zip")
    args = parser.parse_args()

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = args.output_dir or root
    build_portable(args.version.lstrip("v"), out)
