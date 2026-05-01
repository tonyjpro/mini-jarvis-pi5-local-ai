import tkinter as tk
import requests
import json
import threading
from pathlib import Path
from datetime import datetime, timedelta

conversation_history = ""
is_generating = False
MODEL_OPTIONS = {
    "Fast - Qwen 2.5 3B": "qwen2.5:3b-instruct-q8_0",
    "Deep - Qwen 3 8B": "qwen3:8b-q4_K_M",
}
DEFAULT_MODEL_LABEL = "Fast - Qwen 2.5 3B"
MODEL_NAME = MODEL_OPTIONS[DEFAULT_MODEL_LABEL]
LOG_DIR = Path("/home/minijarvis/minijarvis/logs/conversations")
LOG_RETENTION_DAYS = 60

BG_DARK = "#07111f"
BG_PANEL = "#0b1f33"
BG_INPUT = "#102a43"
TEXT_MAIN = "#d7f3ff"
TEXT_MUTED = "#9fbfd0"
ACCENT = "#35d0ff"
ACCENT_DARK = "#145f75"


def cleanup_old_logs():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    cutoff = datetime.now() - timedelta(days=LOG_RETENTION_DAYS)

    for log_file in LOG_DIR.glob("conversation_*.txt"):
        try:
            file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
            if file_time < cutoff:
                log_file.unlink()
        except Exception:
            pass


def append_conversation_log(prompt, response_text, model_label, model_name):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"conversation_{datetime.now().strftime('%Y-%m-%d')}.txt"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with log_path.open("a", encoding="utf-8") as f:
        f.write(f"===== {timestamp} =====\n")
        f.write("MODEL:\n")
        f.write(f"{model_label} -> {model_name}\n\n")
        f.write("USER:\n")
        f.write(prompt.strip() + "\n\n")
        f.write("JARVIS:\n")
        f.write(response_text.strip() + "\n\n")


def stream_ollama(prompt, model_name):
    global conversation_history

    url = "http://127.0.0.1:11434/api/generate"

    full_prompt = f"""
You are a helpful assistant. Answer in clear English only. Keep answers concise (4-5 sentences).

Conversation so far:
{conversation_history}

User: {prompt}
Assistant:
"""

    payload = {
        "model": model_name,
        "prompt": full_prompt,
        "stream": True
    }

    if model_name == "qwen3:8b-q4_K_M":
        payload["think"] = False

    response = requests.post(url, json=payload, stream=True)

    response_text = ""

    for line in response.iter_lines():
        if line:
            data = json.loads(line.decode("utf-8"))
            token = data.get("response", "")
            response_text += token
            yield token

    model_label = next((label for label, exact_name in MODEL_OPTIONS.items() if exact_name == model_name), model_name)
    conversation_history += f"\nUser: {prompt}\nAssistant: {response_text}"
    try:
        append_conversation_log(prompt, response_text, model_label, model_name)
    except Exception as e:
        root.after(0, update_text, f"\n[Warning: conversation log was not saved: {e}]\n")


def run_ollama(prompt, model_name):
    try:
        for token in stream_ollama(prompt, model_name):
            root.after(0, update_text, token)
    except Exception as e:
        root.after(0, update_text, f"\n[Error: {e}]\n")
    finally:
        root.after(0, finish_generation)


def update_text(token):
    text_area.insert(tk.END, token)
    text_area.see(tk.END)


def get_selected_model_label():
    return selected_model_label.get()


def get_selected_model_name():
    return MODEL_OPTIONS[get_selected_model_label()]


def set_status(state, model_label=None):
    if model_label is None:
        model_label = get_selected_model_label()
    status_label.config(text=f"Status: {state} | Model: {model_label}")


def on_model_change(*args):
    if not is_generating:
        set_status("Ready")


def finish_generation():
    global is_generating
    is_generating = False
    send_button.config(state=tk.NORMAL)
    entry.config(state=tk.NORMAL)
    model_menu.config(state=tk.NORMAL)
    set_status("Ready")
    entry.focus()


def send_prompt(event=None):
    global conversation_history
    global is_generating

    if is_generating:
        return

    prompt = entry.get().strip()

    if not prompt:
        return

    entry.delete(0, tk.END)

    if prompt.lower() == "/clear":
        conversation_history = ""
        text_area.insert(tk.END, "\n[Memory cleared]\n")
        text_area.see(tk.END)
        return

    model_label = get_selected_model_label()
    model_name = MODEL_OPTIONS[model_label]

    is_generating = True
    send_button.config(state=tk.DISABLED)
    entry.config(state=tk.DISABLED)
    model_menu.config(state=tk.DISABLED)
    set_status("Thinking", model_label)

    text_area.insert(tk.END, f"\nYou: {prompt}\n")
    text_area.insert(tk.END, "Jarvis is thinking...\n\n")
    text_area.insert(tk.END, "Jarvis: ")
    text_area.see(tk.END)

    thread = threading.Thread(target=run_ollama, args=(prompt, model_name), daemon=True)
    thread.start()


cleanup_old_logs()

root = tk.Tk()
root.title("Mini Jarvis")
root.geometry("900x700")
root.configure(bg=BG_DARK)

selected_model_label = tk.StringVar(value=DEFAULT_MODEL_LABEL)
selected_model_label.trace_add("write", on_model_change)

# Main container
main_frame = tk.Frame(root, bg=BG_DARK)
main_frame.pack(fill=tk.BOTH, expand=True)

# Top frame (text area)
text_frame = tk.Frame(main_frame, bg=BG_DARK)
text_frame.pack(fill=tk.BOTH, expand=True)

scrollbar = tk.Scrollbar(text_frame, bg=BG_PANEL, troughcolor=BG_DARK, activebackground=ACCENT_DARK)

text_area = tk.Text(
    text_frame,
    wrap=tk.WORD,
    yscrollcommand=scrollbar.set,
    font=("Arial", 16),
    bg=BG_DARK,
    fg=TEXT_MAIN,
    insertbackground=ACCENT,
    selectbackground=ACCENT_DARK,
    selectforeground=TEXT_MAIN,
    highlightthickness=0,
    borderwidth=0,
    padx=14,
    pady=14
)
scrollbar.config(command=text_area.yview)

scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Bottom frame (input and send button)
input_frame = tk.Frame(root, bg=BG_PANEL, cursor="left_ptr")
input_frame.pack(fill=tk.X)

entry = tk.Entry(input_frame, font=("Arial", 16), bg=BG_INPUT, fg=TEXT_MAIN, insertbackground=ACCENT, relief=tk.FLAT, highlightthickness=1, highlightbackground=ACCENT_DARK, highlightcolor=ACCENT)
entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 5), pady=10)
entry.bind("<Return>", send_prompt)

model_menu = tk.OptionMenu(input_frame, selected_model_label, *MODEL_OPTIONS.keys())
model_menu.config(
    font=("Arial", 12),
    bg=BG_INPUT,
    fg=TEXT_MAIN,
    activebackground=ACCENT_DARK,
    activeforeground=TEXT_MAIN,
    relief=tk.FLAT,
    highlightthickness=1,
    highlightbackground=ACCENT_DARK,
    cursor="left_ptr",
    width=18
)
model_menu["menu"].config(
    bg=BG_INPUT,
    fg=TEXT_MAIN,
    activebackground=ACCENT_DARK,
    activeforeground=TEXT_MAIN
)
model_menu.pack(side=tk.LEFT, padx=(5, 5), pady=10)

send_button = tk.Button(input_frame, text="Send", font=("Arial", 14), command=send_prompt, cursor="left_ptr", bg=ACCENT_DARK, fg=TEXT_MAIN, activebackground=ACCENT, activeforeground=BG_DARK, relief=tk.FLAT, padx=16, pady=4)
send_button.pack(side=tk.RIGHT, padx=(5, 10), pady=10)

# Status bar
status_frame = tk.Frame(root, bg=BG_PANEL, cursor="left_ptr")
status_frame.pack(fill=tk.X)

status_label = tk.Label(
    status_frame,
    text=f"Status: Ready | Model: {DEFAULT_MODEL_LABEL}",
    anchor="w",
    font=("Arial", 11),
    bg=BG_PANEL,
    fg=TEXT_MUTED,
    padx=10,
    pady=4
)
status_label.pack(fill=tk.X)

text_area.insert(tk.END, "Mini Jarvis is online.\n")
text_area.insert(tk.END, f"Default AI model: {DEFAULT_MODEL_LABEL} -> {MODEL_OPTIONS[DEFAULT_MODEL_LABEL]}\n")
text_area.insert(tk.END, "System mode: Offline local appliance.\n")
text_area.insert(tk.END, "Ready.\n")

entry.focus()

root.mainloop()
