# Local-First AI News Aggregator Agent

Build a Python-based autonomous agent to aggregate, analyze, and catalog news on new AI technologies, model releases, and benchmarks. 

## User Review Required

> [!IMPORTANT]
> - **Ollama Model**: The plan uses the requested model name `gemma4:e4b`. Please ensure you have this specific model pulled in your local Ollama instance (`ollama run gemma4:e4b`). If you meant a different quantization or model tag, let me know.
> - **Serper & Firecrawl**: You will need to obtain free-tier API keys for both Serper.dev and Firecrawl.
> - **Directory**: The project will be created in your current workspace: `c:\Users\rishi\OneDrive\Desktop\web scraping bot`. Let me know if you prefer a different directory.

## Open Questions

> [!WARNING]
> - **RSS Feeds**: I will use a default list of RSS feeds (e.g., OpenAI, DeepMind, Hugging Face blogs). Are there any specific RSS feed URLs you want me to prioritize?
> - **Execution Schedule**: Do you want `main.py` to run continuously on a set interval (e.g., every hour), or just run once per execution? I will default to a single-pass asynchronous execution for now.

## Proposed Changes

### Configuration and Setup

#### [NEW] [.env](file:///c:/Users/rishi/OneDrive/Desktop/web%20scraping%20bot/.env)
Will contain the API keys:
```env
SERPER_API_KEY=your_serper_api_key
FIRECRAWL_API_KEY=your_firecrawl_api_key
OLLAMA_BASE_URL=http://localhost:11434
```

#### [NEW] [requirements.txt](file:///c:/Users/rishi/OneDrive/Desktop/web%20scraping%20bot/requirements.txt)
Will contain all necessary dependencies: `feedparser`, `requests`, `aiohttp`, `pandas`, `openpyxl`, `python-dotenv`.

#### [NEW] [README.md](file:///c:/Users/rishi/OneDrive/Desktop/web%20scraping%20bot/README.md)
Comprehensive documentation explaining the "Local-First" architecture, how the deduplication works using semantic hashing, and step-by-step setup instructions for the Python environment and Ollama.

---

### Core Modules

#### [NEW] [core/__init__.py](file:///c:/Users/rishi/OneDrive/Desktop/web%20scraping%20bot/core/__init__.py)
Empty init file to make it a Python package.

#### [NEW] [core/scout.py](file:///c:/Users/rishi/OneDrive/Desktop/web%20scraping%20bot/core/scout.py)
A multi-threaded/async engine.
- Implements `RSSScout` to fetch raw links from RSS feeds.
- Implements `SearchScout` to query Serper.dev for Google Search and Twitter (site:x.com) specifically targeting AI benchmarks.

#### [NEW] [core/librarian.py](file:///c:/Users/rishi/OneDrive/Desktop/web%20scraping%20bot/core/librarian.py)
Handles extraction.
- Integrates with Firecrawl API to scrape the full content of URLs provided by the Scout and returns clean Markdown.
- Implements robust error handling and retries.

#### [NEW] [core/analyst.py](file:///c:/Users/rishi/OneDrive/Desktop/web%20scraping%20bot/core/analyst.py)
The logic handler.
- Interfaces with local Ollama (`gemma4:e4b`).
- Prompts the LLM with the scraped markdown to extract: Company Name, Model Name, Specific Metrics, and a 1-sentence Innovation Summary.
- Instructs the LLM to generate a short semantic hash/summary of the core innovation to be used for deduplication.
- Returns a structured dictionary (or None if the article is not about a new model/benchmark).

#### [NEW] [core/reporter.py](file:///c:/Users/rishi/OneDrive/Desktop/web%20scraping%20bot/core/reporter.py)
The data-handling module.
- Loads or initializes `ai_intelligence_report.xlsx`.
- Implements deduplication logic by checking the semantic hash against existing entries.
- Appends new, unique data to the Excel file using `pandas` and `openpyxl`.

---

### Orchestration

#### [NEW] [main.py](file:///c:/Users/rishi/OneDrive/Desktop/web%20scraping%20bot/main.py)
The main orchestration script.
- Uses `asyncio` to manage the pipeline.
- Coordinates the flow: Scout -> Librarian -> Analyst -> Reporter.
- Includes error handling to ensure the pipeline continues even if one article fails.

## Verification Plan

### Automated/Manual Testing
1. I will write the code and verify there are no syntax errors.
2. You will need to populate the `.env` file with your API keys and ensure Ollama is running `gemma4:e4b`.
3. You can run `python main.py` to verify the pipeline executes.
4. We will inspect `ai_intelligence_report.xlsx` to confirm data extraction and deduplication are working correctly.
