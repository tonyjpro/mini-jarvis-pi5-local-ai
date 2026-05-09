# Deep Mode Streaming Repair

## Summary

Phase 24 repaired Mini Jarvis Deep Mode latency by changing only the Deep transport path.

Fast Mode remains on the proven Ollama `/api/generate` streaming path.

Deep Mode now uses Ollama `/api/chat` with structured messages, `think:false`, and `stream:true`.

This allows the GUI to display Deep Mode answer text as it is generated instead of waiting silently for the full response to complete.

## Approved Models

Fast Mode:

```text
qwen2.5:3b-instruct-q8_0
```

Deep Mode:

```text
qwen3.5:4b
```

Rejected old Deep model:

```text
qwen3:8b-q4_K_M
```

Do not reintroduce `qwen3:8b-q4_K_M`.

## Transport Design

Fast Mode:

```text
/api/generate
stream:true
```

Deep Mode:

```text
/api/chat
think:false
stream:true
```

Deep Mode reads streamed answer tokens from:

```text
message.content
```

Any model thinking channel content is ignored.

## Thinking Trace Protection

Mini Jarvis must not rely only on prompting or `think:false`.

The application keeps an output-protection layer that removes or suppresses thinking traces before text reaches:

1. The GUI
2. The conversation log

Protection includes:

- stripping complete `<think>...</think>` blocks
- stripping unclosed `<think>` blocks
- stripping stray `</think>` tags
- suppressing streamed `<think>` content before display

## Validation Results

Phase 24 live validation confirmed:

- Fast Mode still streamed normally
- Deep Mode streamed visibly in the GUI
- Deep `/api/chat` direct test succeeded
- No `<think>` or `</think>` tags appeared in the GUI
- No `<think>` or `</think>` tags appeared in the latest conversation log
- Swap remained clean during validation
