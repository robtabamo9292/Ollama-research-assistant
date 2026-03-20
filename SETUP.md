# Setup Guide — Local LLM Research Assistant

A step-by-step guide to get the research assistant running on your machine.

---

## Requirements

- macOS, Windows, or Linux
- Python 3.8 or higher
- ~2GB free disk space
- No internet connection required after setup

---

## Step 1 — Install Ollama

Ollama runs local LLM models on your machine.

**macOS / Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows:**
Download the installer from [ollama.com/download](https://ollama.com/download)

Verify installation:
```bash
ollama --version
```

---

## Step 2 — Pull the Model

```bash
ollama pull qwen2.5:3b
```

This downloads the Qwen2.5 3b model (~1.9GB). Only needs to be done once.

Verify it downloaded:
```bash
ollama list
```

You should see `qwen2.5:3b` in the list.

---

## Step 3 — Start Ollama

```bash
ollama serve
```

If you see `address already in use` — Ollama is already running. That's fine, move on.

---

## Step 4 — Install Python dependency

```bash
pip install pypdf2
```

This is only needed if you plan to analyze PDF files.

---

## Step 5 — Run the assistant

```bash
cd ~/Desktop
python research_assistant.py
```

---

## Usage

Once running, you have two options:

**Option 1 — Analyze a file**

Type the full file path when prompted:
```
/Users/yourname/Desktop/document.pdf
```

Supported file types: `.pdf` `.txt` `.md` `.csv`

**Option 2 — Paste text directly**

Paste any text when prompted, then press Enter twice to analyze.

Type `quit` to exit.

---

## How it works

```
your document or text
        ↓
Stage 1: Qwen2.5:3b — deep structured analysis
        ↓
Stage 2: Qwen2.5:3b — concise executive brief
        ↓
output printed to terminal + saved as JSON
```

Every analysis is automatically saved as a `.json` file in the directory where you ran the script.

---

## Recommended hardware

| Hardware | Performance |
|----------|-------------|
| Apple Silicon (M1/M2/M3) | Fast — 30-60 seconds per analysis |
| Intel Mac / Windows CPU | Slower — 2-3 minutes per analysis |
| 8GB RAM minimum | 16GB recommended |

---

## Troubleshooting

**"Ollama is not running"**
```bash
ollama serve
```

**"File not found"**
Make sure you're using the full file path. On Mac you can drag the file into the terminal to auto-fill the path.

**Timeout error**
Your machine may be running other heavy processes. Close other apps and try again. Alternatively reduce the document size by copying a section of the text and pasting it directly instead of using the full file.

**PDF extracted very little text**
The PDF may be image-based (scanned). Copy and paste the text content directly instead.

---

## Privacy

All processing happens locally on your machine. No data is sent to any external server or API. No internet connection is required after the initial model download.

---

Built by [Robert Tabamo](https://linkedin.com/in/roberttabamo)
