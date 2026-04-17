#!/usr/bin/env python3
"""Download GGUF models to the models/ directory."""

import os
import sys
import urllib.request

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")

RECOMMENDED_MODELS = {
    "1": {
        "name": "Qwen2.5-1.5B-Instruct (Q4_K_M, ~1GB)",
        "url": "https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf",
    },
    "2": {
        "name": "Llama-3.2-1B-Instruct (Q4_K_M, ~0.7GB)",
        "url": "https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF/resolve/main/Llama-3.2-1B-Instruct-Q4_K_M.gguf",
    },
    "3": {
        "name": "Qwen2.5-3B-Instruct (Q4_K_M, ~2GB)",
        "url": "https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf",
    },
}


def download_file(url, dest):
    """Download a file with progress bar."""
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    print(f"Downloading: {os.path.basename(dest)}")
    print(f"URL: {url}\n")

    def show_progress(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            pct = min(downloaded / total_size * 100, 100)
            done = int(pct / 2)
            bar = "=" * done + " " * (50 - done)
            mb_done = downloaded / (1024 * 1024)
            mb_total = total_size / (1024 * 1024)
            print(f"\r  [{bar}] {pct:5.1f}%  ({mb_done:.0f}/{mb_total:.0f} MB)", end="", flush=True)

    urllib.request.urlretrieve(url, dest, show_progress)
    print("\nDone.\n")


def list_models():
    """Print recommended models."""
    print("\n=== Recommended Models ===")
    for key, info in RECOMMENDED_MODELS.items():
        print(f"  [{key}] {info['name']}")
    print()


def download_cli():
    """Interactive download CLI entry point."""
    os.makedirs(MODELS_DIR, exist_ok=True)

    print("=== Model Downloader ===")
    list_models()
    print("  [4] Enter custom URL")
    print()

    choice = input("Select option: ").strip()

    if choice in RECOMMENDED_MODELS:
        info = RECOMMENDED_MODELS[choice]
        filename = info["url"].split("/")[-1]
        dest = os.path.join(MODELS_DIR, filename)
        download_file(info["url"], dest)
    elif choice == "4":
        url = input("Enter HuggingFace GGUF URL: ").strip()
        filename = url.split("/")[-1]
        if not filename.lower().endswith(".gguf"):
            print("Warning: URL does not appear to be a .gguf file")
            confirm = input("Continue anyway? (y/n): ").strip().lower()
            if confirm != "y":
                return
        dest = os.path.join(MODELS_DIR, filename)
        download_file(url, dest)
    else:
        print("Invalid choice.")
        return

    # Update config with downloaded model
    import json
    config_path = os.path.join(BASE_DIR, "config.json")
    config = {}
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    config["model_path"] = filename
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    print(f"\nConfig updated: default model = {filename}")


def main():
    if len(sys.argv) > 1:
        url = sys.argv[1]
        filename = url.split("/")[-1]
        dest = os.path.join(MODELS_DIR, filename)
        download_file(url, dest)
    else:
        download_cli()


if __name__ == "__main__":
    main()
