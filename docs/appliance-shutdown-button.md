# Appliance Shutdown Button

Mini Jarvis now includes an appliance-style shutdown control in the desktop GUI.

## Purpose

Mini Jarvis is intended to behave like a local AI appliance. A user should not need to open Terminal and manually run a shutdown command to power down the Raspberry Pi safely.

Closing the GUI window with the window close button is not the same as shutting down the Raspberry Pi. It may close only the Tkinter application window while leaving Debian, Ollama, and system services running.

The new GUI shutdown button provides a safer and clearer appliance workflow.

## User workflow

1. Click **Shutdown** in the Mini Jarvis GUI.
2. Confirm the dialog.
3. Click **Cancel** to return to Mini Jarvis without shutting down, or click **Shut Down** to safely power off the Raspberry Pi.
4. Wait for the Raspberry Pi to reach its halted state.
5. On Raspberry Pi 5 hardware or compatible cases with a power button, the physical button can be used to wake or boot the Pi again after shutdown.

## GUI placement

The shutdown button is placed on the bottom control row:

- Status on the left.
- Shutdown in the center.
- Model selector on the right.

The prompt input field remains on its own row above the control row, reducing the chance of accidental shutdown while typing a question.

## Security model

Mini Jarvis uses a tightly scoped sudoers rule. The GUI does not receive broad passwordless sudo privileges.

The GUI runs this dedicated helper:

    sudo /usr/local/sbin/mini-jarvis-shutdown

The helper script path is:

    /usr/local/sbin/mini-jarvis-shutdown

Reference helper contents:

    #!/usr/bin/env bash
    set -euo pipefail
    /usr/sbin/shutdown -h now

The sudoers rule concept is:

    minijarvis ALL=(root) NOPASSWD: /usr/local/sbin/mini-jarvis-shutdown

This permits only that one shutdown helper to run without a password. It does not permit arbitrary passwordless sudo commands.

## Files

Live Raspberry Pi helper path:

    /usr/local/sbin/mini-jarvis-shutdown

Live Raspberry Pi sudoers path:

    /etc/sudoers.d/mini-jarvis-shutdown

Repository reference helper:

    startup/mini-jarvis-shutdown

Repository sudoers reference:

    system-reference/mini-jarvis-shutdown-sudoers.conf

GUI file:

    app/jarvis_ui.py

## Validation performed

Phase 26 validation confirmed:

- Shutdown button appears in the GUI.
- Confirmation dialog appears.
- Cancel leaves Mini Jarvis running.
- Fast Mode still works.
- Deep Mode still works.
- Deep Mode thinking cleanup still works.
- Real shutdown works without a password prompt.
- Raspberry Pi reboots successfully using the physical power button after shutdown.
- Mini Jarvis and Ollama recover successfully after reboot.
