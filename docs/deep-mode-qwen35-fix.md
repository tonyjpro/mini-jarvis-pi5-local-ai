# Deep Mode Fix: Qwen3.5 4B and Thinking-Trace Protection

## Overview

Mini Jarvis originally used `qwen3:8b-q4_K_M` as its Deep model. During post-submission testing on Raspberry Pi 5 with Ollama 0.22.0, that model proved unreliable in this setup.

The validated Deep mode replacement is `qwen3.5:4b`.

Current model mapping:

- Fast - Qwen 2.5 3B -> `qwen2.5:3b-instruct-q8_0`
- Deep - Qwen 3.5 4B -> `qwen3.5:4b`

## Problem Observed

The original Deep model mapping was `Deep - Qwen 3 8B -> qwen3:8b-q4_K_M`.

During GUI testing, Deep mode returned to Ready but did not display an answer. Direct Ollama diagnostics showed the problem was not the GUI, storage, memory pressure, or the `think:false` setting. The failure was isolated to the Ollama/model layer.

The old Deep model returned HTTP 500 errors. Ollama logs showed a GGUF-related panic similar to `runtime error: makeslice: len out of range` in `github.com/ollama/ollama/fs/gguf/gguf.go`.

After re-pulling and restarting Ollama, `qwen3:8b-q4_K_M` still failed in this Mini Jarvis Raspberry Pi 5 / Ollama 0.22.0 setup. For this project, that model path is treated as known-bad and should not be used as the public Deep mode default.

## Validated Fix

The validated replacement Deep model is `qwen3.5:4b`.

Required model pull:

```bash
ollama pull qwen3.5:4b
ollama show qwen3.5:4b
```

## Code Changes

The GUI model mapping was changed to use `Deep - Qwen 3.5 4B` and `qwen3.5:4b`.

The GUI now includes `clean_model_response()` to remove thinking traces and `is_deep_model()` to identify the Deep model path.

Deep mode now collects the full response first, cleans it, and only then displays the final answer. Fast mode preserves streaming behavior.

## Thinking-Trace Protection

Qwen-family models may expose thinking traces. Mini Jarvis should not rely only on prompting or Ollama `think:false` to suppress those traces.

The application layer must also clean model output before it reaches the GUI display or conversation log.

The cleaner strips `<think>...</think>`, unclosed `<think>` blocks, stray `</think>` tags, and case variants such as `<THINK>`.

## Manual Validation Checklist

1. Confirm Fast model availability with `ollama show qwen2.5:3b-instruct-q8_0`.
2. Confirm Deep model availability with `ollama show qwen3.5:4b`.
3. Test Fast mode from the GUI.
4. Test Deep mode from the GUI.
5. Run a thinking-leak prompt that tries to force visible `<think>` tags.
6. Confirm the GUI displays only the final cleaned answer.
7. Confirm no thinking tags appear in assistant responses written to the conversation log.

## Log Verification

When scanning logs, avoid false positives caused by user prompts that mention `<think>` tags. The important check is whether the actual assistant response section contains leaked thinking traces.

Expected result: no `<think>...</think>` blocks, no unclosed `<think>` blocks, no stray `</think>` tags, and no thinking traces written to conversation logs as assistant output.

## Status

Status: validated in Mini Jarvis Phase 21G and synchronized into the public GitHub package in Phase 21H.

The public Deep mode default is now `qwen3.5:4b`.

The old broken public Deep model mapping `qwen3:8b-q4_K_M` has been removed from `app/jarvis_ui.py`.
