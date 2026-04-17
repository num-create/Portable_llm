#!/usr/bin/env python3
"""Interactive terminal chat interface for local GGUF models.

Uses llama-server for persistent model loading (no reload per message).
Streaming output with token speed display.
"""

import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
import urllib.error

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
    INTERNAL_DIR = os.path.join(BASE_DIR, "_internal")
    if os.path.isdir(INTERNAL_DIR):
        LLAMA_SERVER = os.path.join(INTERNAL_DIR, "llama-server.exe")
    else:
        LLAMA_SERVER = os.path.join(BASE_DIR, "llama-server.exe")
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    LLAMA_SERVER = os.path.join(BASE_DIR, "llama-server.exe")

MODELS_DIR = os.path.join(BASE_DIR, "models")
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
KB_DIR = os.path.join(BASE_DIR, "kb")

SERVER_URL = "http://127.0.0.1:8190"
SERVER_PORT = 8190

# KB content cache (refresh on /kb reload)
KB_CACHE = {}

HELP_TEXT = '\n\
  Commands:\n\
    /help or /h        - Show this help\n\
    /quit or /q        - Exit the program\n\
    /reset or /r       - Clear conversation history\n\
    /clear or /c       - Clear screen (keep history)\n\
    /config            - Show current settings\n\
    /kb                - List knowledge base files\n\
    /kb on <file>      - Enable a KB file\n\
    /kb off <file>     - Disable a KB file\n\
    /kb all            - Enable all KB files\n\
    /kb none           - Disable all KB files\n\
    /kb reload         - Rescan kb/ directory\n\
    """                - Start multiline input (end with """)\n'

# === KB management ===

def scan_kb_files():
    if not os.path.isdir(KB_DIR):
        return []
    return sorted(f for f in os.listdir(KB_DIR) if f.lower().endswith((".txt", ".md")))


def read_kb_file(fname):
    """Read KB file with caching."""
    if fname in KB_CACHE:
        return KB_CACHE[fname]
    fpath = os.path.join(KB_DIR, fname)
    try:
        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
            KB_CACHE[fname] = content
            return content
    except IOError:
        return ""


def clear_kb_cache():
    """Clear KB cache for reload."""
    global KB_CACHE
    KB_CACHE = {}


def build_kb_text(enabled_files):
    parts = []
    for fname in sorted(enabled_files):
        content = read_kb_file(fname)
        if content:
            parts.append(f"--- {fname} ---\n{content}")
    return "\n".join(parts) if parts else ""


def get_enabled_kb_files():
    all_files = scan_kb_files()
    if not all_files:
        return []
    enabled = None
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                user_cfg = json.load(f)
            enabled = user_cfg.get("kb_enabled")
        except (json.JSONDecodeError, IOError):
            pass
    if enabled is not None:
        return [f for f in all_files if f in enabled]
    return all_files


def save_kb_enabled(enabled_files):
    all_files = scan_kb_files()
    config = {}
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    if set(enabled_files) == set(all_files):
        config["kb_enabled"] = None
    else:
        config["kb_enabled"] = [f for f in enabled_files]
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


# === Config ===

def save_config(config):
    """Save config to file."""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def load_config():
    defaults = {
        "model_path": "",
        "n_ctx": 2048,
        "max_tokens": 512,
        "temperature": 0.7,
        "top_p": 0.9,
        "repeat_penalty": 1.1,
        "system_prompt": "You are a helpful assistant.",
        "n_threads": 0,
        "n_predict": 512,
    }
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                user_cfg = json.load(f)
            defaults.update(user_cfg)
        except (json.JSONDecodeError, IOError):
            pass
    return defaults


# === Model ===

def scan_models():
    if not os.path.isdir(MODELS_DIR):
        os.makedirs(MODELS_DIR, exist_ok=True)
        return []
    return [f for f in os.listdir(MODELS_DIR) if f.lower().endswith(".gguf")]


def select_model(models, config):
    if not models:
        print("\nNo models found in models/ directory.")
        print(f"Place .gguf files in: {MODELS_DIR}")
        print("\nPress Enter to exit...")
        input()
        sys.exit(1)
    print("\n=== Available Models ===")
    for i, name in enumerate(models, 1):
        size_mb = os.path.getsize(os.path.join(MODELS_DIR, name)) / (1024 * 1024)
        print(f"  {i}. {name}  ({size_mb:.0f} MB)")
    print()
    while True:
        choice = input("Select model (number): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(models):
            model_file = models[int(choice) - 1]
            # Auto-save model choice
            if config.get("model_path") != model_file:
                config["model_path"] = model_file
                save_config(config)
            return model_file
        print("Invalid choice, try again.")


# === Server management ===

def check_port(port):
    """Check if a port is already in use."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(("127.0.0.1", port))
        return True
    except (ConnectionRefusedError, OSError):
        return False
    finally:
        s.close()


def api_get(path, timeout=5):
    url = f"{SERVER_URL}{path}"
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def start_server(model_path, config):
    n_threads = config["n_threads"] or os.cpu_count() or 4
    model_full = os.path.join(MODELS_DIR, model_path)

    if not os.path.exists(LLAMA_SERVER):
        print(f"Error: llama-server.exe not found at {LLAMA_SERVER}")
        return None

    if check_port(SERVER_PORT):
        print(f"Port {SERVER_PORT} is already in use. Close any program using it and try again.")
        return None

    cmd = [
        LLAMA_SERVER,
        "--model", model_full,
        "--threads", str(n_threads),
        "--port", str(SERVER_PORT),
        "--host", "127.0.0.1",
        "--ctx-size", str(config["n_ctx"]),
        "--repeat-penalty", str(config["repeat_penalty"]),
        "--temp", str(config["temperature"]),
        "--top-p", str(config["top_p"]),
        "--threads-batch", str(max(n_threads * 2, 8)),
    ]

    print(f"Starting llama-server (threads={n_threads})...")
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    print("Loading model, please wait...", end="", flush=True)
    wait_time = 0
    check_interval = 0.3  # Start fast, then slow down
    max_interval = 1.5
    for _ in range(600):  # 180+ seconds with adaptive intervals
        time.sleep(check_interval)
        wait_time += check_interval
        if proc.poll() is not None:
            print(f"\nServer failed to start after {wait_time:.0f}s. Exit code: {proc.poll()}")
            return None
        try:
            api_get("/health", timeout=2)
            print(f" Ready ({wait_time:.0f}s).")
            return proc
        except (urllib.error.URLError, OSError, ConnectionError):
            # Show progress
            if wait_time >= 5 and int(wait_time) % 5 == 0:
                print(f" {int(wait_time)}s", end="", flush=True)
            else:
                print(".", end="", flush=True)
            # Slow down checks after initial period (exponential backoff)
            if wait_time < 5:
                check_interval = 0.3  # Fast initial checks
            elif wait_time < 30:
                check_interval = 0.5
            elif wait_time < 60:
                check_interval = 1.0
            else:
                check_interval = min(check_interval * 1.2, max_interval)

    print(f"\nServer startup timed out after {wait_time:.0f}s.")
    proc.kill()
    return None


def read_multiline():
    """Read multi-line input using triple-quote delimiter."""
    lines = []
    print("Multiline mode (end with \"\"\"):")
    while True:
        try:
            line = input()
        except (EOFError, KeyboardInterrupt):
            return ""
        if line == '"""':
            break
        lines.append(line)
    return "\n".join(lines)


def server_chat(system_prompt, n_predict, config, enabled_files):
    kb = build_kb_text(enabled_files)
    current_system = f"{system_prompt}\n\n以下是参考资料，请根据这些知识回答问题：\n{kb}" if kb else system_prompt
    messages = [{"role": "system", "content": current_system}]
    n_threads = config["n_threads"] or os.cpu_count() or 4

    print(f"Model loaded. (threads={n_threads})\n")
    print("=== Chat (type /help for commands) ===\n")

    while True:
        # Show KB status in prompt
        kb_count = len(enabled_files)
        prompt = f"You [kb:{kb_count}]: " if kb_count > 0 else "You: "
        try:
            user_input = input(prompt)
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        # Handle multiline input with """
        if user_input.strip() == '"""':
            user_input = read_multiline()
            if not user_input:
                continue
        else:
            user_input = user_input.strip()

        if not user_input:
            continue
        cmd_lower = user_input.lower()
        # Command shortcuts
        if cmd_lower in ("quit", "exit", "/quit", "/q"):
            print("Bye!")
            break
        if cmd_lower in ("help", "/help", "/h"):
            print(HELP_TEXT)
            continue
        if cmd_lower in ("/reset", "/r"):
            messages = [{"role": "system", "content": current_system}]
            print("(History cleared)\n")
            continue
        if cmd_lower in ("/clear", "/c"):
            os.system('cls' if os.name == 'nt' else 'clear')
            print("=== Chat (type /help for commands) ===\n")
            continue
        if user_input.lower() == "/kb" or user_input.lower().startswith("/kb "):
            enabled_files, current_system = handle_kb_command(
                user_input, enabled_files, system_prompt
            )
            # Update system prompt in place without clearing history
            messages[0] = {"role": "system", "content": current_system}
            continue
        if user_input.lower() == "/config":
            active_kb = [f for f in enabled_files if f in scan_kb_files()]
            print(f"  temperature={config['temperature']}")
            print(f"  max_tokens={n_predict}")
            print(f"  top_p={config['top_p']}")
            print(f"  repeat_penalty={config['repeat_penalty']}")
            print(f"  n_ctx={config['n_ctx']}")
            print(f"  threads={n_threads}")
            print(f"  kb_active={active_kb if active_kb else 'none'}")
            print()
            continue

        messages.append({"role": "user", "content": user_input})

        try:
            req = urllib.request.Request(
                f"{SERVER_URL}/v1/chat/completions",
                data=json.dumps({
                    "messages": messages,
                    "max_tokens": n_predict,
                    "temperature": config["temperature"],
                    "top_p": config["top_p"],
                    "repeat_penalty": config["repeat_penalty"],
                    "stream": True,
                }).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            start_time = time.time()
            print("Assistant: ", end="", flush=True)
            assistant_msg = ""
            token_count = 0

            with urllib.request.urlopen(req, timeout=300) as resp:
                while True:
                    line = resp.readline().decode("utf-8")
                    if not line:
                        break
                    line = line.strip()
                    if line.startswith("data: "):
                        payload = line[6:]
                        if payload == "[DONE]":
                            break
                        try:
                            chunk = json.loads(payload)
                            delta = chunk["choices"][0]["delta"]
                            content = delta.get("content", "")
                            if content:
                                print(content, end="", flush=True)
                                assistant_msg += content
                                token_count += 1
                        except (json.JSONDecodeError, KeyError):
                            pass

            elapsed = time.time() - start_time
            speed = token_count / elapsed if elapsed > 0 else 0
            print(f"\n  [{token_count} tokens, {speed:.1f} tok/s]\n")

            messages.append({"role": "assistant", "content": assistant_msg})

            # Smart context trimming: keep system prompt + last N exchanges
            max_messages = config.get("max_history_messages", 16)
            if len(messages) > max_messages:
                messages = [messages[0]] + messages[-(max_messages - 1):]

        except (urllib.error.URLError, ConnectionError, OSError) as e:
            print(f"\nServer error: {e}\n")
        except Exception as e:
            print(f"\nError: {e}\n")

    return None


def handle_kb_command(cmd, enabled_files, system_prompt_base):
    parts = cmd.split(None, 2)
    action = parts[1].lower() if len(parts) > 1 else ""
    all_files = scan_kb_files()

    def build_system():
        kb = build_kb_text(enabled_files)
        return f"{system_prompt_base}\n\n以下是参考资料，请根据这些知识回答问题：\n{kb}" if kb else system_prompt_base

    if action == "" or action == "list":
        if not all_files:
            print("  No KB files found in kb/\n")
            return enabled_files, build_system()
        print("  KB Files:")
        for f in all_files:
            status = "ON" if f in enabled_files else "OFF"
            size = os.path.getsize(os.path.join(KB_DIR, f))
            print(f"    [{status}] {f}  ({size} bytes)")
        print(f"\n  Usage: /kb on <file> | /kb off <file> | /kb all | /kb none | /kb reload\n")
        return enabled_files, build_system()

    elif action == "on" and len(parts) >= 3:
        fname = parts[2].strip()
        if fname not in all_files:
            print(f"  File not found: {fname}\n")
            return enabled_files, build_system()
        if fname not in enabled_files:
            enabled_files.append(fname)
            save_kb_enabled(enabled_files)
        print(f"  Enabled: {fname}\n")
        return enabled_files, build_system()

    elif action == "off" and len(parts) >= 3:
        fname = parts[2].strip()
        if fname in enabled_files:
            enabled_files.remove(fname)
            save_kb_enabled(enabled_files)
        print(f"  Disabled: {fname}\n")
        return enabled_files, build_system()

    elif action == "all":
        enabled_files = list(all_files)
        save_kb_enabled(enabled_files)
        print(f"  All {len(enabled_files)} KB file(s) enabled\n")
        return enabled_files, build_system()

    elif action == "none":
        enabled_files = []
        save_kb_enabled(enabled_files)
        print("  All KB files disabled\n")
        return enabled_files, system_prompt_base

    elif action == "reload":
        clear_kb_cache()
        all_files = scan_kb_files()
        enabled_files = [f for f in enabled_files if f in all_files]
        print(f"  Reloaded: {len(enabled_files)} file(s) active\n")
        return enabled_files, build_system()

    return enabled_files, system_prompt_base


def main():
    config = load_config()

    if not os.path.exists(LLAMA_SERVER):
        print(f"Error: llama-server.exe not found in {BASE_DIR}")
        print("Place llama-server.exe and its DLLs in the same folder.")
        print("\nPress Enter to exit...")
        input()
        sys.exit(1)

    available = scan_models()
    if config.get("model_path"):
        cfg_model = config["model_path"]
        if os.path.exists(os.path.join(MODELS_DIR, cfg_model)):
            model_file = cfg_model
            print(f"Using saved model: {cfg_model}\n")
        elif available:
            model_file = select_model(available, config)
        else:
            print(f"Configured model not found: {cfg_model}")
            print("\nPress Enter to exit...")
            input()
            sys.exit(1)
    else:
        model_file = select_model(available, config)

    kb_files = get_enabled_kb_files()
    if kb_files:
        print(f"Knowledge base: {len(kb_files)} file(s) active")
        for f in kb_files:
            size = os.path.getsize(os.path.join(KB_DIR, f))
            print(f"  {f}  ({size} bytes)")
    else:
        print("Knowledge base: none (use /kb to manage)")
    print()

    system_prompt_base = config.get("system_prompt", "You are a helpful assistant.")

    # Start llama-server
    server_proc = start_server(model_file, config)
    if server_proc is None:
        print("Failed to start llama-server. Exiting.")
        print("\nPress Enter to exit...")
        input()
        sys.exit(1)

    try:
        server_chat(system_prompt_base, config.get("n_predict", config["max_tokens"]), config, kb_files)
    finally:
        print("\nShutting down llama-server...")
        server_proc.kill()
        server_proc.wait()


if __name__ == "__main__":
    main()
