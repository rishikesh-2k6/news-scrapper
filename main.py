import asyncio
from dotenv import load_dotenv

from core.scout import gather_all_links
from core.librarian import Librarian
from core.analyst import Analyst
from core.reporter import Reporter

async def process_link(link_info, librarian, analyst, reporter):
    url = link_info.get("link")
    title = link_info.get("title")
    print(f"\n--- Processing: {title} ---")
    
    # 1. Scrape Content
    markdown = await librarian.extract_markdown(url)
    if not markdown:
        print("-> Skipping: No markdown content extracted.")
        return

    # 2. Analyze Content with LLM
    analysis_result = await analyst.analyze_article(markdown, url)
    if not analysis_result:
        print("-> Skipping: Not relevant or analysis failed.")
        return

    # 3. Report & Deduplicate
    added = reporter.add_entry(analysis_result)
    if added:
        print("-> Success: Entry added to intelligence report.")
    else:
        print("-> Skipped: Duplicate entry or error.")

async def main():
    print("=== Starting AI Intelligence Pipeline ===")
    
    # Load Environment Variables
    load_dotenv()

    # Initialize Modules
    librarian = Librarian()
    analyst = Analyst()
    reporter = Reporter()

    # Step 1: Scout for Links
    print("\n[Phase 1] Scouting for raw links...")
    links = await gather_all_links()
    print(f"Found {len(links)} total links to process.")

    # Step 2: Process each link sequentially to avoid overwhelming local LLM/APIs
    # (For a true local LLM, concurrency would crash the VRAM, so sequential is safer)
    print("\n[Phase 2] Analyzing and Cataloging...")
    for link_info in links:
        await process_link(link_info, librarian, analyst, reporter)

    print("\n=== AI Intelligence Pipeline Complete ===")

if __name__ == "__main__":
    asyncio.run(main())
