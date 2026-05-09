import tkinter as tk
import requests
import json
import threading
import subprocess
import re
from tkinter import messagebox
from pathlib import Path
from datetime import datetime, timedelta

conversation_history = ""
is_generating = False
MODEL_OPTIONS = {
    "Fast - Qwen 2.5 3B": "qwen2.5:3b-instruct-q8_0",
    "Deep - Qwen 3.5 4B": "qwen3.5:4b",
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



def clean_model_response(text):
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<think>.*$", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"</think>", "", text, flags=re.IGNORECASE)
    return text.strip()


def is_deep_model(model_name):
    return model_name == "qwen3.5:4b"


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

    response_text = ""

    if is_deep_model(model_name):
        url = "http://127.0.0.1:11434/api/chat"

        system_message = (
            "You are a helpful assistant. Answer the user's latest message directly. "
            "Answer in clear English only. Keep answers concise unless the user asks for detail. "
            "Do not output hidden reasoning, analysis traces, thinking content, or <think> blocks. "
            "Give only the final answer."
        )

        messages = [
            {
                "role": "system",
                "content": system_message
            }
        ]

        if conversation_history.strip():
            messages.append(
                {
                    "role": "user",
                    "content": "Recent conversation context, for reference only:\n" + conversation_history.strip()
                }
            )

        messages.append(
            {
                "role": "user",
                "content": prompt
            }
        )

        payload = {
            "model": model_name,
            "messages": messages,
            "think": False,
            "stream": True
        }

        response = requests.post(url, json=payload, stream=True)
        response.raise_for_status()

        in_think_block = False
        pending_tag = ""

        def filter_visible_text(piece):
            nonlocal in_think_block
            nonlocal pending_tag

            visible = []

            for ch in piece:
                if in_think_block:
                    if pending_tag:
                        pending_tag += ch
                        lower_tag = pending_tag.lower()
                        if "</think>".startswith(lower_tag):
                            if lower_tag == "</think>":
                                in_think_block = False
                                pending_tag = ""
                        else:
                            pending_tag = ""
                    elif ch == "<":
                        pending_tag = "<"
                    continue

                if pending_tag:
                    pending_tag += ch
                    lower_tag = pending_tag.lower()
                    if "<think>".startswith(lower_tag):
                        if lower_tag == "<think>":
                            in_think_block = True
                            pending_tag = ""
                    else:
                        visible.append(pending_tag)
                        pending_tag = ""
                    continue

                if ch == "<":
                    pending_tag = "<"
                else:
                    visible.append(ch)

            return "".join(visible)

        for line in response.iter_lines():
            if not line:
                continue

            data = json.loads(line.decode("utf-8"))

            message = data.get("message", {})
            token = message.get("content", "")

            if token:
                visible_token = filter_visible_text(token)
                if visible_token:
                    response_text += visible_token
                    yield visible_token

            if data.get("done"):
                break

        response_text = clean_model_response(response_text)

    else:
        url = "http://127.0.0.1:11434/api/generate"

        full_prompt = f"""
You are a helpful assistant. Answer in clear English only. Keep answers concise (4-5 sentences). Do not output thinking tags, hidden reasoning, analysis traces, or <think> blocks.

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

        response = requests.post(url, json=payload, stream=True)
        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                data = json.loads(line.decode("utf-8"))
                token = data.get("response", "")
                response_text += token
                yield token

        response_text = clean_model_response(response_text)

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



def confirm_shutdown():
    dialog = tk.Toplevel(root)
    dialog.title("Shut down Mini Jarvis?")
    dialog.configure(bg=BG_PANEL)
    dialog.resizable(False, False)
    dialog.transient(root)
    dialog.grab_set()

    container = tk.Frame(dialog, bg=BG_PANEL, padx=24, pady=18)
    container.pack(fill=tk.BOTH, expand=True)

    title_label = tk.Label(
        container,
        text="Shut down Mini Jarvis?",
        font=("Arial", 16, "bold"),
        bg=BG_PANEL,
        fg=TEXT_MAIN
    )
    title_label.pack(pady=(0, 8))

    message_label = tk.Label(
        container,
        text="This will safely power off the Raspberry Pi.",
        font=("Arial", 12),
        bg=BG_PANEL,
        fg=TEXT_MUTED
    )
    message_label.pack(pady=(0, 18))

    button_frame = tk.Frame(container, bg=BG_PANEL)
    button_frame.pack(fill=tk.X)

    def cancel_shutdown():
        dialog.destroy()

    def run_shutdown():
        try:
            shutdown_button.config(state=tk.DISABLED)
            set_status("Shutting down")
            subprocess.Popen(["sudo", "/usr/local/sbin/mini-jarvis-shutdown"])
            dialog.destroy()
        except Exception as exc:
            shutdown_button.config(state=tk.NORMAL)
            messagebox.showerror("Shutdown failed", f"Mini Jarvis could not start shutdown:\n{exc}")
            set_status("Ready")

    cancel_button = tk.Button(
        button_frame,
        text="Cancel",
        font=("Arial", 12),
        command=cancel_shutdown,
        cursor="left_ptr",
        bg=BG_INPUT,
        fg=TEXT_MAIN,
        activebackground=ACCENT_DARK,
        activeforeground=TEXT_MAIN,
        relief=tk.FLAT,
        padx=14,
        pady=5
    )
    cancel_button.pack(side=tk.LEFT, padx=(0, 10))

    confirm_button = tk.Button(
        button_frame,
        text="Shut Down",
        font=("Arial", 12, "bold"),
        command=run_shutdown,
        cursor="left_ptr",
        bg=ACCENT_DARK,
        fg=TEXT_MAIN,
        activebackground=ACCENT,
        activeforeground=BG_DARK,
        relief=tk.FLAT,
        padx=14,
        pady=5
    )
    confirm_button.pack(side=tk.RIGHT)

    dialog.update_idletasks()
    root_x = root.winfo_rootx()
    root_y = root.winfo_rooty()
    root_w = root.winfo_width()
    root_h = root.winfo_height()
    dialog_w = dialog.winfo_width()
    dialog_h = dialog.winfo_height()
    pos_x = root_x + (root_w // 2) - (dialog_w // 2)
    pos_y = root_y + (root_h // 2) - (dialog_h // 2)
    dialog.geometry(f"+{pos_x}+{pos_y}")
    dialog.wait_window()


cleanup_old_logs()

root = tk.Tk()
root.title("Mini Jarvis")
root.geometry("1000x760")
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

send_button = tk.Button(input_frame, text="Send", font=("Arial", 14), command=send_prompt, cursor="left_ptr", bg=ACCENT_DARK, fg=TEXT_MAIN, activebackground=ACCENT, activeforeground=BG_DARK, relief=tk.FLAT, padx=16, pady=4)
send_button.pack(side=tk.RIGHT, padx=(5, 10), pady=10)

# Status and appliance control bar
status_frame = tk.Frame(root, bg=BG_PANEL, cursor="left_ptr")
status_frame.pack(fill=tk.X)
status_frame.grid_columnconfigure(0, weight=1)
status_frame.grid_columnconfigure(1, weight=0)
status_frame.grid_columnconfigure(2, weight=1)

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
status_label.grid(row=0, column=0, sticky="ew", padx=(0, 8))

shutdown_button = tk.Button(
    status_frame,
    text="Shutdown",
    font=("Arial", 11),
    command=confirm_shutdown,
    cursor="left_ptr",
    bg=BG_INPUT,
    fg=TEXT_MAIN,
    activebackground=ACCENT_DARK,
    activeforeground=TEXT_MAIN,
    relief=tk.FLAT,
    padx=14,
    pady=3
)
shutdown_button.grid(row=0, column=1, padx=24, pady=5)

model_menu = tk.OptionMenu(status_frame, selected_model_label, *MODEL_OPTIONS.keys())
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
model_menu.grid(row=0, column=2, sticky="e", padx=(8, 10), pady=5)

text_area.insert(tk.END, "Mini Jarvis is online.\n")
text_area.insert(tk.END, f"Default AI model: {DEFAULT_MODEL_LABEL} -> {MODEL_OPTIONS[DEFAULT_MODEL_LABEL]}\n")
text_area.insert(tk.END, "System mode: Offline local appliance.\n")
text_area.insert(tk.END, "Ready.\n")

entry.focus()

root.mainloop()
