# Social Pulse

AI-powered social listening agent that collects public web mentions and performs field-level sentiment analysis.

This repository is a working prototype designed for a take-home assignment. It demonstrates clean modular architecture, reliable LLM integration, and actionable outputs without production overhead.

## Features
- 🔍 Collects public web content via Google Search (SerpAPI)
- 🧠 Field-level sentiment analysis using Google Gemini 2.5 Flash
- 📊 Simple aggregation and Markdown report output
- 🧪 Pydantic data models with type hints
- 🛠️ CLI pipeline for end-to-end execution

## Architecture Overview
High-level flow: Data Source → Collector → Analyzer → Report

- Collector: `GoogleSearchCollector` queries SerpAPI and normalizes results to `RawItem`
- Analyzer: `SentimentAnalyzer` (Gemini) returns `AnalyzedItem` with field-level sentiments
- Report: Markdown summary with overall and per-field counts

See also:
- spec.md — technical specification and data models (updated with current state)
- AGENTS.md — architecture and planning (updated snapshot and decisions)

## Requirements
- Python 3.10+
- SerpAPI account and API key
- Google Gemini API key
 - Optional: pydantic-ai (for future Agent wiring)

## Installation
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Optional (Agent wiring experiments):
```bash
pip install pydantic-ai
```

## Configuration
Create a `.env` file in the project root with:
```bash
SERPAPI_KEY=your_serpapi_key
GOOGLE_API_KEY=your_gemini_key
```

Optional environment variables:
- `LOG_LEVEL` (DEBUG, INFO, WARNING, ERROR, CRITICAL) – default: INFO
 - If wiring pydantic-ai Agent later: set provider keys accordingly (e.g., `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`).

## Usage
Run from the project root and use module execution so Python recognizes the `src` package.

- End-to-end pipeline:
```bash
python -m src.main --all --limit 30 --analyze-limit 10
```

- Only collect:
```bash
python -m src.main --collect --limit 30
```

- Only analyze (uses outputs/items.json if not provided in-memory):
```bash
python -m src.main --analyze --analyze-limit 10
```

- Only report (uses outputs/analyzed.json if not provided in-memory):
```bash
python -m src.main --report
```

## Outputs
- `outputs/items.json` — raw collected `RawItem` list
- `outputs/analyzed.json` — analyzed `AnalyzedItem` list
- `outputs/report.md` — human-readable summary

## Troubleshooting
- ImportError: No module named `src`
  - Always run with `python -m src.main` from the project root.
- Empty or partial results
  - Ensure `SERPAPI_KEY` is valid and not rate-limited.
- Analyzer errors
  - Ensure `GOOGLE_API_KEY` is set. The analyzer now validates LLM JSON against a strict Pydantic schema (`AnalysisResult`) and retries once with an explicit schema reminder on invalid output. API remains stable.

## Provider Options (Analyzer)

- Default: Gemini via `google-generativeai` (current, cost-effective, good JSON adherence)
- Optional (future): pydantic-ai Agent using
  - OpenAI (requires `OPENAI_API_KEY`), or
  - Anthropic (requires `ANTHROPIC_API_KEY`)

The validation layer keeps the public API unchanged. If you wire the Agent, prefer a try-Agent-then-fallback-to-Gemini pattern.

## Recommended Tests (added)

- Analyzer retry path: first attempt returns invalid JSON; second returns valid schema → expect success.
- Agent fallback (if wired): simulate Agent failure then verify Gemini path produces a valid `AnalyzedItem`.

## Contributing
This is a focused prototype. Feel free to open issues or PRs that:
- Improve reliability (rate-limit handling, retries)
- Add new collectors (Reddit via PRAW, LinkedIn scraping)
- Introduce a dedicated aggregation module and a simple UI

## License
MIT

