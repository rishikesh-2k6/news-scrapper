# AI News Aggregator Agent (Local-First)

A Python-based autonomous agent that aggregates, analyzes, and catalogs news on new AI technologies, model releases, and benchmarks. 

This project is built with a **Local-First Architecture**, ensuring privacy, avoiding massive API costs for LLM inference, and demonstrating proficiency in handling hardware constraints.

## Architecture

1.  **Scout (`core/scout.py`)**: A multi-threaded engine that fetches raw links from a list of RSS feeds (OpenAI, Google DeepMind, Hugging Face) and uses Serper.dev to search Google and Twitter for AI benchmarks.
2.  **Librarian (`core/librarian.py`)**: Uses Firecrawl to scrape the full content of "high-interest" links found by the Scout and converts them into clean Markdown.
3.  **Analyst (`core/analyst.py`)**: The logic handler. It interfaces with a local LLM via Ollama (`gemma4:e4b` with 4-bit quantization). It analyzes the Markdown to identify new benchmarks or models, extracting the Company Name, Model Name, Specific Metrics, and an Innovation Summary. It also generates a semantic hash for deduplication.
4.  **Reporter (`core/reporter.py`)**: Handles data storage. It checks the semantic hash against existing entries to prevent duplicates, and appends new, unique data to a formatted `ai_intelligence_report.xlsx` file.
5.  **Main (`main.py`)**: An asynchronous orchestration script that runs the entire pipeline.

## Prerequisites

- Python 3.9+
- [Ollama](https://ollama.com/) installed and running locally.
- Free-tier API keys for [Serper.dev](https://serper.dev/) and [Firecrawl](https://firecrawl.dev/).

## Setup Instructions

1.  **Install Python Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configure Environment Variables:**
    Open the `.env` file and add your API keys:
    ```env
    SERPER_API_KEY=your_serper_api_key
    FIRECRAWL_API_KEY=your_firecrawl_api_key
    OLLAMA_BASE_URL=http://localhost:11434
    ```

3.  **Pull the Local LLM:**
    Ensure Ollama is running, then pull the target Gemma 4 model (or your preferred local model):
    ```bash
    ollama run gemma4:e4b
    ```
    *Note: Adjust the model name in `core/analyst.py` if you use a different tag.*

4.  **Run the Agent:**
    Execute the main pipeline:
    ```bash
    python main.py
    ```

## Deduplication Logic

The agent uses **Semantic Hashing** to ensure the same news from different sources is merged into a single entry. The local Gemma model is prompted to extract the core essence of the innovation (e.g., "Llama-3-70B-Release") which acts as a unique identifier before saving to the `.xlsx` report.
