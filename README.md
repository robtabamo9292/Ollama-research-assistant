# Local LLM Research Assistant: Ollama

A local AI research assistant built with Ollama that runs a two-stage analysis pipeline using DeepSeek-R1 and Qwen2.5. Runs entirely on local hardware — no API keys, no data leaving the machine.

---

## Models used

- **DeepSeek-R1** — strong reasoning and document analysis
- **Qwen2.5** — efficient summarization and structured extraction

---

## What it does

- Ingests research documents (PDFs, markdown, text files)
- Extracts key insights, themes, and data points
- Generates structured research briefs from raw inputs
- Translates quantitative signals into plain-language summaries

---

## Why local?

Running models locally means:
- **No data exposure** — sensitive research stays on-device
- **No API costs** — run thousands of document analyses for free
- **Full control** — swap models, adjust parameters, no rate limits

This mirrors the privacy-first approach required in regulated industries like healthcare, where data sovereignty is non-negotiable.

---

## Setup

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull models
ollama pull deepseek-r1
ollama pull qwen2.5

# Run a model
ollama run deepseek-r1
```

---

## Workflow

```
raw documents (PDFs, text, data)
        ↓
  preprocessing (chunking, cleaning)
        ↓
  Ollama local inference (DeepSeek / Qwen)
        ↓
  structured research brief
```

---

## Use cases

- Summarizing long-form research reports into actionable briefs
- Extracting structured data points from unstructured documents
- Comparing multiple sources and identifying contradictions
- Automating repetitive document review tasks

---

## Skills demonstrated

- Local LLM deployment and model management
- Prompt engineering for document analysis tasks
- Workflow automation with AI tools
- Privacy-conscious AI architecture

---

Built by [Robert Tabamo](https://linkedin.com/in/roberttabamo)
