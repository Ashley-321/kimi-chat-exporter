# Kimi Chat Exporter

Export your entire [Kimi](https://www.kimi.com) conversation history to clean Markdown files — no third-party services, no data leaving your machine.

**Requirements:** Python 3.8+ &nbsp;·&nbsp; No extra packages (standard library only)

---

## Quick Start

```bash
git clone https://github.com/YOUR_USERNAME/kimi-chat-exporter.git
cd kimi-chat-exporter
python exporters/kimi_exporter.py --token "YOUR_TOKEN_HERE"
```

---

## Step 1 — Get your token

1. Open [kimi.com](https://www.kimi.com) and log in
2. Press **F12** → **Console** tab
3. Paste and run:
   ```javascript
   copy(localStorage.getItem('access_token') || localStorage.getItem('refresh_token'))
   ```
4. Your token is now in the clipboard

---

## Step 2 — Run the exporter

```bash
python exporters/kimi_exporter.py --token "YOUR_TOKEN_HERE"
```

All conversations are saved to `~/Desktop/kimi_exports/` as individual `.md` files.

### Options

| Flag | Default | Description |
|---|---|---|
| `--token` | *(required)* | Your Kimi access token |
| `--output` | `~/Desktop/kimi_exports` | Output directory |
| `--delay` | `0.5` | Seconds between requests (increase if rate-limited) |

---

## Output Format

Each conversation is saved as a separate Markdown file:

```
0001_What is the speed of light.md
0002_Python async tutorial.md
0003_Untitled.md
...
```

File content example:

```markdown
# What is the speed of light

> **Exported**: 2025-12-01 14:30:00
> **Chat ID**: `abc123`
> **Messages**: 4

---

### 👤 User

What is the speed of light?

---

### 🤖 Kimi

The speed of light in a vacuum is approximately **299,792,458 meters per second** (m/s)...

---
```

---

## Privacy & Security

- **Your data never leaves your machine.** The script communicates directly with Kimi's API using your own credentials.
- **No token is stored.** The token is passed as a command-line argument and is never written to disk by this tool.
- **Open source.** Read the code yourself — it's under 300 lines.

> ⚠️ Keep your token private. Anyone with this value can access your Kimi account. Tokens typically expire after 30 days.

---

## Limitations

- **Token expiry.** If you get a `401` error, your token has expired — repeat Step 1 to get a fresh one.
- **Rate limiting.** Use `--delay 1.0` or higher if requests start failing.
- **Message count.** The exporter fetches up to 500 messages per conversation. For extremely long chats, some early messages may be truncated.

---

## Contributing

Pull requests are welcome! Ideas:
- Add support for other AI platforms
- Export to HTML or PDF
- Progress resume (skip already-exported files)

---

## License

MIT
