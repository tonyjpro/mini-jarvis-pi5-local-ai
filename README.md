# Mini Jarvis Raspberry Pi 5 Local AI Appliance

Mini Jarvis is a local AI appliance built on a Raspberry Pi 5. It runs a desktop graphical interface that connects to local Ollama language models, allowing prompts and responses to stay on the device without cloud dependency.

This repository contains the cleaned project code, startup files, reference configuration files, and documentation for review and download.

## Project Purpose

Mini Jarvis was built to explore whether a Raspberry Pi 5 can function as a small, practical, local AI terminal.

The goal was not just to run a model once, but to create an appliance-like system that can:

- Boot into a usable AI interface
- Run locally without cloud dependency
- Use Ollama for local inference
- Provide a simple graphical interface
- Stream responses into the window
- Keep a fast model ready by default
- Allow a deeper model to be selected
- Log conversations locally
- Maintain a rolling 60-day log history
- Start automatically through systemd

## Hardware Platform

Primary hardware:

- Raspberry Pi 5 Model B Rev 1.1
- 16GB RAM
- USB-C SSD storage
- Active cooling
- HDMI display
- USB keyboard and mouse
- Official Raspberry Pi 5 27W USB-C power supply recommended

The system documented here uses an external SSD rather than a USB thumb drive. For AI workloads and appliance reliability, SSD storage is strongly preferred.

## Software Platform

Documented software baseline:

- Debian GNU/Linux 13, trixie
- Raspberry Pi kernel 6.12.75+rpt-rpi-2712
- Python 3.13.5
- Tkinter GUI
- Ollama 0.22.0
- systemd user service startup
- Local Ollama API at `http://127.0.0.1:11434/api/generate`

## Approved Models

The Mini Jarvis GUI supports two approved models:

| GUI Label | Ollama Model | Purpose |
|---|---|---|
| Fast - Qwen 2.5 3B | `qwen2.5:3b-instruct-q8_0` | Default fast model |
| Deep - Qwen 3.5 4B | `qwen3.5:4b` | Validated Deep mode replacement |

TinyLlama is installed in the documented build but intentionally hidden from the GUI because it was not approved for the final user-facing experience.

## Deep Mode Update

During post-submission testing, the original Deep model mapping, `qwen3:8b-q4_K_M`, proved unreliable in the Raspberry Pi 5 / Ollama 0.22.0 environment used by Mini Jarvis. The validated Deep mode replacement is now `qwen3.5:4b`.

Because Qwen-family models may expose `<think>...</think>` reasoning traces, Mini Jarvis does not rely only on prompting or Ollama `think:false`. The GUI also includes an output-layer cleaner that strips thinking traces before displaying responses or writing conversation logs.

See `docs/deep-mode-qwen35-fix.md` for the full fix details and validation checklist.

## Repository Structure

```text
mini-jarvis-pi5-local-ai/
├── README.md
├── app/
│   └── jarvis_ui.py
├── startup/
│   ├── start_all.sh
│   └── jarvis.service
├── requirements/
│   └── requirements.txt
├── system-reference/
│   ├── boot-cmdline.txt
│   └── ollama-override.conf
├── docs/
│   ├── Mini Jarvis - Official Canonical Project Documentation ver 2.rtf
│   ├── Mini_Jarvis_Key_Files_Explained_Current.rtf
│   ├── Mini_Jarvis_Phase_17R_D3_Storage_Stability_Addendum.rtf
│   └── Mini_Jarvis_Source_Code_Addendum_Needs_Codefiles.rtf
└── screenshots/
```

## Key Files

### `app/jarvis_ui.py`

The main Mini Jarvis application.

It handles:

- Tkinter GUI
- User input
- Streaming responses
- Model dropdown
- Fast and Deep model selection
- Status bar
- Conversation memory
- Conversation logging
- 60-day log cleanup
- Qwen3.5 Deep mode response cleaning and `think:false` API behavior
- Non-fatal logging protection

### `startup/start_all.sh`

Startup script used by the systemd service.

It:

- Sets the display environment
- Enters the Mini Jarvis project directory
- Activates the Python virtual environment
- Waits for system stabilization
- Warms the default Qwen2.5 model
- Launches `jarvis_ui.py`

### `startup/jarvis.service`

The systemd user service that starts Mini Jarvis automatically under the user session.

### `requirements/requirements.txt`

Python package dependencies used inside the Mini Jarvis virtual environment.

Tkinter is not installed through pip. It is supplied by operating system packages.

### `system-reference/ollama-override.conf`

Reference copy of the Ollama systemd override used to keep loaded models resident:

```text
OLLAMA_KEEP_ALIVE=24h
```

### `system-reference/boot-cmdline.txt`

Reference copy of the Raspberry Pi boot command line after the USB SSD stability patch.

This file includes:

```text
usb-storage.quirks=152d:0562:u
```

This was added to force a JMicron USB SSD bridge to use the more stable `usb-storage` driver instead of UAS.

## Conversation Logs

Conversation logs are stored on the live Mini Jarvis system at:

```text
/home/minijarvis/minijarvis/logs/conversations/
```

Daily files use this pattern:

```text
conversation_YYYY-MM-DD.txt
```

The repository intentionally does not include conversation logs.

## Important Storage Stability Note

During hardening, the system showed an intermittent storage issue with a JMicron USB-to-SATA bridge:

```text
152d:0562 JMicron JMS567 SATA 6Gb/s bridge
```

Symptoms included:

- Conversation log I/O warning
- Partial desktop degradation
- SSH instability
- Boot halt behavior
- UAS abort and USB reset messages in kernel logs

The fix was to add this boot option:

```text
usb-storage.quirks=152d:0562:u
```

After reboot, the kernel confirmed:

```text
UAS is ignored for this device, using usb-storage instead
```

This is documented in the storage stability addendum inside the `docs/` folder.

## What Is Included

This repository includes:

- Main GUI source code
- Startup script
- systemd user service
- Python requirements
- Reference boot command line
- Reference Ollama keep-alive override
- Project documentation

## What Is Not Included

This repository intentionally excludes:

- Conversation logs
- SSH keys
- Wi-Fi credentials
- Passwords
- `.env` files
- Ollama model blobs
- Virtual environments
- Cache folders
- Raw home folder content
- Private or personal files

## How to Review or Download

Readers can review the files directly in GitHub.

To download:

1. Click the green **Code** button.
2. Choose **Download ZIP**.

To clone:

```bash
git clone https://github.com/YOUR-GITHUB-USERNAME/mini-jarvis-pi5-local-ai.git
```

Replace `YOUR-GITHUB-USERNAME` with the final GitHub account name once the repository is published.

## Project Status

Current documented state:

- Stable local AI appliance
- Post Phase 17R
- Post Phase 17R-D3 USB SSD UAS stability patch
- Prepared for public review and download

## Notes for Readers

This project is shared as a learning and review package. It is not a one-click installer. The documentation is included to explain the build decisions, architecture, hardening steps, and operational lessons learned.

The most important practical lesson from the build is that a Raspberry Pi 5 local AI appliance can work well, but storage reliability, cooling, startup automation, and model behavior all matter.

## Deep Mode Streaming Repair

Mini Jarvis Deep Mode now uses Ollama `/api/chat` with `think:false` and `stream:true`, while Fast Mode remains on the proven `/api/generate` streaming path.

This repair prevents the GUI from appearing frozen during Deep Mode responses and preserves the mandatory app-level thinking-trace cleanup before display and logging.

See: `docs/deep-mode-streaming-repair.md`
