"""
Local LLM Research Assistant — Upgraded
Built with Ollama + Python data processing

Features:
  - Document analysis (PDF, TXT, MD)
  - Excel / CSV data analysis with statistics
  - Chart generation (saves as PNG)
  - Live crypto/stock price lookups
  - General Q&A
  - All processing local — no data leaves your machine

Usage:
  python research_assistant.py

Commands:
  /path/to/file.pdf     — analyze a document
  /path/to/file.xlsx    — analyze a spreadsheet
  /path/to/file.csv     — analyze CSV data
  price bitcoin         — get live crypto price
  chart /path/file.csv  — generate a chart from CSV/Excel
  (any text)            — general Q&A with Qwen

Author: Robert Tabamo
"""

import json
import urllib.request
import urllib.error
import sys
import os
from datetime import datetime


# ── Auto-install dependencies ──────────────────────────────────────────────────

def install_if_missing(package, import_name=None):
    import importlib
    try:
        importlib.import_module(import_name or package)
    except ImportError:
        print(f"Installing {package}...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", package, "-q"])


# ── Ollama ─────────────────────────────────────────────────────────────────────

def check_ollama():
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags")
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        print("Ollama is not running. Start it with: ollama serve")
        sys.exit(1)


def query_ollama(prompt: str, system: str = "", timeout: int = 180) -> str:
    payload = {"model": "qwen2.5:3b", "prompt": prompt, "stream": False}
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


# ── System Prompts ─────────────────────────────────────────────────────────────

ANALYSIS_SYSTEM = """
You are a rigorous research analyst. When given any document, article, or data:
1. Identify the core argument or main findings
2. Extract key data points and supporting evidence
3. Flag any gaps, assumptions, or weak reasoning
4. Assess reliability of the information
5. Structure your response with clearly labeled sections
Be precise. Cite specific details. Distinguish facts from interpretations.
"""

SUMMARY_SYSTEM = """
You are a concise research summarizer. Distill complex analysis into plain language.
Format:
- Takeaway: one sentence main finding
- Key Points: 3-5 bullet points
- Action Items: what to do with this information
- Confidence: High / Medium / Low and brief reason
Keep under 200 words. Clarity over completeness.
"""

DATA_SYSTEM = """
You are a data analyst. You are given a statistical summary of a dataset.
Interpret the data clearly:
1. Describe what the dataset contains
2. Highlight the most important patterns or trends
3. Flag any anomalies or outliers
4. Suggest what questions this data could answer
5. Note any limitations or missing context
Be specific. Reference actual numbers from the summary.
"""

QA_SYSTEM = """
You are a knowledgeable research assistant. Answer questions clearly and concisely.
- For factual questions: give a direct answer with context
- For analytical questions: structure your response with clear reasoning
- Always acknowledge uncertainty when you are not sure
- Keep responses focused and under 300 words unless more detail is needed
"""


# ── File Readers ───────────────────────────────────────────────────────────────

def read_pdf(path: str) -> str:
    install_if_missing("pypdf2", "PyPDF2")
    try:
        import PyPDF2
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        if len(text.strip()) < 100:
            print("Warning: very little text extracted. PDF may be image-based.")
            print("Try copying and pasting the text directly.")
            return None
        return text.strip()
    except Exception as e:
        print(f"Could not read PDF: {e}")
        return None


def read_text_file(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read().strip()


def read_spreadsheet(path: str) -> tuple:
    """
    Read Excel or CSV file.
    Returns (summary_text, dataframe) for analysis and charting.
    """
    install_if_missing("pandas")
    install_if_missing("openpyxl")

    try:
        import pandas as pd

        ext = os.path.splitext(path)[1].lower()
        if ext == ".csv":
            df = pd.read_csv(path)
        else:
            df = pd.read_excel(path)

        # Build a text summary for the LLM
        lines = []
        lines.append(f"Dataset: {os.path.basename(path)}")
        lines.append(f"Rows: {len(df)}, Columns: {len(df.columns)}")
        lines.append(f"Columns: {', '.join(df.columns.tolist())}")
        lines.append("")

        # Data types
        lines.append("Column types:")
        for col, dtype in df.dtypes.items():
            lines.append(f"  {col}: {dtype}")
        lines.append("")

        # Numeric stats
        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        if numeric_cols:
            lines.append("Numeric statistics:")
            stats = df[numeric_cols].describe().round(2)
            lines.append(stats.to_string())
            lines.append("")

        # Sample rows
        lines.append("First 5 rows:")
        lines.append(df.head(5).to_string())
        lines.append("")

        # Missing values
        missing = df.isnull().sum()
        missing = missing[missing > 0]
        if len(missing) > 0:
            lines.append("Missing values:")
            for col, count in missing.items():
                lines.append(f"  {col}: {count} missing")

        return "\n".join(lines), df

    except Exception as e:
        print(f"Could not read spreadsheet: {e}")
        return None, None


# ── Chart Generation ───────────────────────────────────────────────────────────

def generate_chart(df, output_path: str = None) -> str:
    """
    Auto-generate the most appropriate chart for the dataset.
    Saves as PNG and returns the file path.
    """
    install_if_missing("matplotlib")

    try:
        import pandas as pd
        import matplotlib
        matplotlib.use("Agg")  # non-interactive backend
        import matplotlib.pyplot as plt

        if not output_path:
            output_path = f"chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

        import pandas as pd
        df = df.copy()
        for col in df.columns:
            if "date" in col.lower() or "time" in col.lower():
                try:
                    df[col] = pd.to_datetime(df[col])
                    df = df.set_index(col)
                    break
                except Exception:
                    pass

        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        if not numeric_cols:
            return "No numeric columns found for charting."

        is_time_index = str(df.index.dtype) == "datetime64[ns]"
        n = min(len(numeric_cols), 3)
        fig, axes = plt.subplots(n, 1, figsize=(12, 4 * n))
        if n == 1:
            axes = [axes]

        for i, col in enumerate(numeric_cols[:3]):
            ax = axes[i]
            if is_time_index:
                ax.plot(df.index, df[col], color="#1f77b4", linewidth=2, marker="o", markersize=5)
                fig.autofmt_xdate()
            elif df[col].nunique() <= 10:
                df[col].value_counts().sort_index().plot(ax=ax, kind="bar", color="#1f77b4")
                ax.tick_params(axis="x", rotation=45)
            else:
                ax.plot(range(len(df)), df[col], color="#1f77b4", linewidth=2, marker="o", markersize=5)
            ax.set_title(col, fontsize=12, fontweight="bold")
            ax.set_xlabel("")
            ax.grid(axis="y", alpha=0.3)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)

        plt.suptitle("Data Overview", fontsize=13, fontweight="bold")
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()

        return output_path

    except Exception as e:
        return f"Chart error: {e}"


# ── Live Price Lookup ──────────────────────────────────────────────────────────

def get_price(query: str) -> str:
    """
    Fetch live crypto price from CoinGecko API (free, no key required).
    """
    # Map common names to CoinGecko IDs
    coin_map = {
        "bitcoin": "bitcoin", "btc": "bitcoin",
        "ethereum": "ethereum", "eth": "ethereum",
        "solana": "solana", "sol": "solana",
        "cardano": "cardano", "ada": "cardano",
        "xrp": "ripple", "ripple": "ripple",
        "dogecoin": "dogecoin", "doge": "dogecoin",
        "polygon": "matic-network", "matic": "matic-network",
        "chainlink": "chainlink", "link": "chainlink",
        "avalanche": "avalanche-2", "avax": "avalanche-2",
        "polkadot": "polkadot", "dot": "polkadot",
        "uniswap": "uniswap", "uni": "uniswap",
        "litecoin": "litecoin", "ltc": "litecoin",
    }

    token = query.lower().strip()
    coin_id = coin_map.get(token, token)

    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_change=true&include_market_cap=true"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))

        if coin_id not in data:
            return f"Could not find price for '{query}'. Try the full coin name (e.g. 'solana', 'bitcoin')."

        info = data[coin_id]
        price = info.get("usd", "N/A")
        change = info.get("usd_24h_change", 0)
        mcap = info.get("usd_market_cap", 0)

        change_str = f"+{change:.2f}%" if change >= 0 else f"{change:.2f}%"
        mcap_str = f"${mcap:,.0f}" if mcap else "N/A"

        return (
            f"\n{'─'*40}\n"
            f"  {query.upper()} — Live Price\n"
            f"{'─'*40}\n"
            f"  Price      : ${price:,.4f}\n"
            f"  24h Change : {change_str}\n"
            f"  Market Cap : {mcap_str}\n"
            f"{'─'*40}\n"
            f"  Source: CoinGecko  |  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        )

    except Exception as e:
        return f"Could not fetch price: {e}. Check your internet connection."


# ── Core Analysis Pipeline ─────────────────────────────────────────────────────

def analyze_document(text: str) -> None:
    if len(text) > 4000:
        print(f"Note: Input trimmed to 4000 characters (was {len(text)})")
        text = text[:4000]

    print(f"\n{'='*60}")
    print("ANALYZING DOCUMENT...")
    print(f"{'='*60}")
    print(f"Input  : {len(text)} characters")
    print(f"Time   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    print("\n[Stage 1] Deep analysis — Qwen2.5:3b...")
    analysis = query_ollama(
        f"Analyze the following document in detail:\n\n---\n{text}\n---",
        ANALYSIS_SYSTEM
    )
    print("✓ Complete")

    print(f"\n{'─'*60}")
    print("DEEP ANALYSIS:")
    print("─"*60)
    print(analysis)

    print(f"\n[Stage 2] Executive brief — Qwen2.5:3b...")
    brief = query_ollama(
        f"Summarize this analysis into a concise executive brief:\n\n---\n{analysis}\n---",
        SUMMARY_SYSTEM,
        timeout=120
    )
    print("✓ Complete")

    print(f"\n{'─'*60}")
    print("EXECUTIVE BRIEF:")
    print("─"*60)
    print(brief)

    output = {
        "timestamp": datetime.now().isoformat(),
        "type": "document_analysis",
        "input_length": len(text),
        "deep_analysis": analysis,
        "executive_brief": brief
    }
    output_file = f"output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved to: {output_file}")


def analyze_data(path: str, make_chart: bool = False) -> None:
    print(f"\n{'='*60}")
    print("ANALYZING DATA...")
    print(f"{'='*60}")
    print(f"File: {os.path.basename(path)}")

    summary, df = read_spreadsheet(path)
    if summary is None:
        return

    print(f"✓ Loaded ({len(df)} rows x {len(df.columns)} columns)")

    # Generate chart if requested
    if make_chart and df is not None:
        print("\n[Generating chart...]")
        chart_path = generate_chart(df)
        if chart_path and not chart_path.startswith("Chart error"):
            print(f"✓ Chart saved: {chart_path}")
        else:
            print(f"Chart note: {chart_path}")

    # LLM interprets the data
    print("\n[Analyzing with Qwen2.5:3b...]")
    interpretation = query_ollama(
        f"Interpret this dataset summary:\n\n---\n{summary[:3000]}\n---",
        DATA_SYSTEM
    )
    print("✓ Complete")

    print(f"\n{'─'*60}")
    print("DATA INTERPRETATION:")
    print("─"*60)
    print(interpretation)

    # Save
    output = {
        "timestamp": datetime.now().isoformat(),
        "type": "data_analysis",
        "file": os.path.basename(path),
        "rows": len(df),
        "columns": len(df.columns),
        "interpretation": interpretation
    }
    output_file = f"data_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved to: {output_file}")


def answer_question(question: str) -> None:
    print(f"\n{'='*60}")
    print("ANSWERING...")
    print(f"{'='*60}")

    response = query_ollama(question, QA_SYSTEM)
    print(f"\n{response}")


# ── Entry Point ────────────────────────────────────────────────────────────────

def main():
    print("="*60)
    print("Local LLM Research Assistant")
    print("Qwen2.5:3b via Ollama | Built by Robert Tabamo")
    print("Private. Local. No data leaves your machine.")
    print("="*60)
    print("\nWhat you can do:")
    print("  /path/to/file.pdf       — analyze a document")
    print("  /path/to/file.xlsx      — analyze a spreadsheet")
    print("  /path/to/file.csv       — analyze CSV data")
    print("  chart /path/to/file     — analyze + generate chart")
    print("  price bitcoin           — live crypto price")
    print("  price solana            — live crypto price")
    print("  (any question or text)  — general Q&A")
    print("  quit                    — exit\n")

    check_ollama()

    while True:
        print("─"*60)
        print("INPUT:")

        try:
            user_input = input().strip()
        except EOFError:
            break

        if not user_input:
            continue

        if user_input.lower() == "quit":
            print("Exiting.")
            sys.exit(0)

        # ── Price lookup
        if user_input.lower().startswith("price "):
            token = user_input[6:].strip()
            print(get_price(token))
            continue

        # ── Chart command
        if user_input.lower().startswith("chart "):
            path = os.path.expanduser(user_input[6:].strip())
            ext = os.path.splitext(path)[1].lower()
            if ext in [".csv", ".xlsx", ".xls"]:
                analyze_data(path, make_chart=True)
            else:
                print("Chart command works with .csv and .xlsx files only.")
            continue

        # ── File path
        stripped = user_input
        if stripped.startswith("/") or stripped.startswith("~"):
            expanded = os.path.expanduser(stripped)
            ext = os.path.splitext(expanded)[1].lower()

            if not os.path.exists(expanded):
                print(f"File not found: {expanded}")
                continue

            if ext == ".pdf":
                print(f"Reading PDF: {expanded}")
                content = read_pdf(expanded)
                if content:
                    print(f"✓ Loaded ({len(content)} characters)")
                    analyze_document(content)
                continue

            elif ext in [".txt", ".md"]:
                content = read_text_file(expanded)
                print(f"✓ Loaded ({len(content)} characters)")
                analyze_document(content)
                continue

            elif ext in [".csv", ".xlsx", ".xls"]:
                analyze_data(expanded, make_chart=False)
                print("\nTip: type 'chart " + expanded + "' to also generate a chart.")
                continue

            else:
                print(f"Unsupported file type: {ext}")
                continue

        # ── Multi-line paste (press Enter twice)
        if "\n" in user_input or len(user_input) > 200:
            analyze_document(user_input)
            continue

        # ── General Q&A
        answer_question(user_input)

        print("\n" + "="*60)
        print("Ready. Type a question, file path, or command.")


if __name__ == "__main__":
    main()
