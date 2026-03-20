"""
Local LLM Research Assistant
Built with Ollama — runs entirely on local hardware

Uses Qwen2.5:3b for both deep analysis and summarization.
Optimized for Intel CPU machines.

Usage:
  python research_assistant.py

Accepts:
  - File path (PDF, TXT, markdown, CSV)
  - Pasted text directly

No API keys. No internet. No data leaves your machine.

Author: Robert Tabamo
"""

import json
import urllib.request
import urllib.error
import sys
import os
from datetime import datetime


# ── Dependencies ───────────────────────────────────────────────────────────────

def install_if_missing(package, import_name=None):
    import importlib
    try:
        importlib.import_module(import_name or package)
    except ImportError:
        print(f"Installing {package}...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", package, "-q"])


# ── Ollama Connection ──────────────────────────────────────────────────────────

def check_ollama():
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags")
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        print("Ollama is not running. Start it with: ollama serve")
        sys.exit(1)


def query_ollama(model: str, prompt: str, system: str = "", timeout: int = 180) -> str:
    payload = {"model": model, "prompt": prompt, "stream": False}
    if system:
        payload["system"] = system
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            "http://localhost:11434/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result.get("response", "").strip()
    except urllib.error.URLError as e:
        return f"Connection error: {e}"
    except Exception as e:
        return f"Error: {str(e)}"


# ── File Reader ────────────────────────────────────────────────────────────────

def read_file(path: str) -> str:
    path = path.strip().strip("'\"")
    expanded = os.path.expanduser(path)

    if not os.path.exists(expanded):
        print(f"File not found: {expanded}")
        return None

    ext = os.path.splitext(expanded)[1].lower()

    if ext == ".pdf":
        install_if_missing("pypdf2", "PyPDF2")
        try:
            import PyPDF2
            with open(expanded, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
            if len(text.strip()) < 100:
                print("Warning: very little text extracted. Try pasting content directly.")
                return None
            return text.strip()
        except Exception as e:
            print(f"Could not read PDF: {e}")
            return None

    elif ext in [".txt", ".md", ".csv"]:
        with open(expanded, "r", encoding="utf-8", errors="ignore") as f:
            return f.read().strip()

    else:
        print(f"Unsupported file type: {ext}. Supported: .pdf .txt .md .csv")
        return None


# ── System Prompts ─────────────────────────────────────────────────────────────

ANALYSIS_SYSTEM = """
You are a rigorous research analyst. When given any document, article, data, or text:

1. Identify the core argument or main findings
2. Extract key data points and supporting evidence
3. Flag any gaps, assumptions, or weak reasoning
4. Assess the reliability of the information
5. Structure your response with clearly labeled sections

Be precise. Cite specific details. Distinguish facts from interpretations.
"""

SUMMARY_SYSTEM = """
You are a concise research summarizer. Distill complex analysis into plain language.

Format your response exactly as:
- Takeaway: one sentence main finding
- Key Points: 3-5 bullet points
- Action Items: what to do with this information
- Confidence: High / Medium / Low and brief reason

Keep under 200 words. Clarity over completeness.
"""


# ── Core Pipeline ──────────────────────────────────────────────────────────────

def analyze(text: str) -> None:
    if len(text) > 4000:
        print(f"Note: Input trimmed to 4000 characters (was {len(text)})")
        text = text[:4000]

    print(f"\n{'='*60}")
    print("ANALYZING...")
    print(f"{'='*60}")
    print(f"Input  : {len(text)} characters")
    print(f"Time   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Stage 1 — Deep analysis
    print("\n[Stage 1] Deep analysis — Qwen2.5:3b...")
    analysis = query_ollama(
        "qwen2.5:3b",
        f"Analyze the following document in detail:\n\n---\n{text}\n---",
        ANALYSIS_SYSTEM,
        timeout=180
    )
    print("✓ Complete")

    print(f"\n{'─'*60}")
    print("DEEP ANALYSIS:")
    print("─"*60)
    print(analysis)

    # Stage 2 — Executive brief
    print(f"\n[Stage 2] Executive brief — Qwen2.5:3b...")
    brief = query_ollama(
        "qwen2.5:3b",
        f"Summarize this analysis into a concise executive brief:\n\n---\n{analysis}\n---",
        SUMMARY_SYSTEM,
        timeout=120
    )
    print("✓ Complete")

    print(f"\n{'─'*60}")
    print("EXECUTIVE BRIEF:")
    print("─"*60)
    print(brief)

    # Save
    output = {
        "timestamp": datetime.now().isoformat(),
        "input_length": len(text),
        "deep_analysis": analysis,
        "executive_brief": brief
    }
    output_file = f"output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved to: {output_file}")


# ── Entry Point ────────────────────────────────────────────────────────────────

def main():
    print("="*60)
    print("Local LLM Research Assistant")
    print("Qwen2.5:3b via Ollama")
    print("Private. Local. No data leaves your machine.")
    print("="*60)
    print("\nOptions:")
    print("  1. Type a file path (.pdf .txt .md .csv)")
    print("  2. Paste text directly, press Enter twice when done")
    print("  3. Type 'quit' to exit\n")

    check_ollama()

    while True:
        print("─"*60)
        print("INPUT:")
        lines = []
        while True:
            try:
                line = input()
            except EOFError:
                break

            if line.lower() == "quit":
                print("Exiting.")
                sys.exit(0)

            stripped = line.strip()
            if len(lines) == 0 and (
                stripped.startswith("/") or
                stripped.startswith("~") or
                stripped.endswith(".pdf") or
                stripped.endswith(".txt") or
                stripped.endswith(".md") or
                stripped.endswith(".csv")
            ):
                expanded = os.path.expanduser(stripped)
                print(f"Reading: {expanded}")
                content = read_file(expanded)
                if content:
                    print(f"✓ Loaded ({len(content)} characters)")
                    analyze(content)
                else:
                    print("Could not read file. Try pasting the text directly.")
                lines = []
                break

            if line == "" and lines and lines[-1] == "":
                break
            lines.append(line)

        if lines:
            text = "\n".join(lines).strip()
            if text:
                analyze(text)

        print("\n" + "="*60)
        print("Ready. File path or paste text. Type 'quit' to exit.")


if __name__ == "__main__":
    main()
