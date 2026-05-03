import asyncio
import time
import psutil
from core.scout import gather_all_links
from core.librarian import Librarian
from core.analyst import Analyst
from core.reporter import Reporter

class AgentRunner:
    def __init__(self):
        self.librarian = Librarian()
        self.analyst = Analyst()
        self.reporter = Reporter()
        self.is_running = False
        self.status = "Stopped"
        self.stop_event = asyncio.Event()

    async def start(self):
        if self.is_running:
            return
        self.is_running = True
        self.stop_event.clear()
        self.status = "Starting..."
        print("[AgentRunner] Background agent started.")
        # Start the background task
        asyncio.create_task(self._run_loop())

    async def stop(self):
        self.is_running = False
        self.status = "Stopping..."
        self.stop_event.set()
        print("[AgentRunner] Stop signal sent to background agent.")

    async def get_status(self):
        battery = psutil.sensors_battery()
        plugged = battery.power_plugged if battery else True
        return {
            "status": self.status,
            "battery_plugged": plugged
        }

    async def _process_link(self, link_info):
        if self.stop_event.is_set():
            return
            
        url = link_info.get("link")
        title = link_info.get("title")
        print(f"\n--- Processing: {title} ---")
        
        markdown = await self.librarian.extract_markdown(url)
        if not markdown or self.stop_event.is_set():
            return

        analysis_result = await self.analyst.analyze_article(markdown, url)
        if not analysis_result or self.stop_event.is_set():
            return

        self.reporter.add_entry(analysis_result)

    async def _run_loop(self):
        start_time = time.time()
        # Run for 6 hours max per session
        while time.time() - start_time < 6 * 3600:
            if self.stop_event.is_set():
                break

            battery = psutil.sensors_battery()
            is_plugged = battery.power_plugged if battery else True

            if not is_plugged:
                self.status = "Paused (On Battery)"
                print("[AgentRunner] Laptop on battery. Pausing for 1 minute...")
                await asyncio.sleep(60)
                continue

            self.status = "Running"
            print("\n[Phase 1] Scouting for raw links...")
            links = await gather_all_links()
            
            print(f"\n[Phase 2] Analyzing {len(links)} links...")
            for link_info in links:
                if self.stop_event.is_set():
                    break
                # Process links sequentially to avoid OOM on local GPU
                await self._process_link(link_info)

            if self.stop_event.is_set():
                break
                
            self.status = "Sleeping (Next run in 30 mins)"
            print("\n[AgentRunner] Pipeline complete. Sleeping for 30 minutes...")
            
            # Sleep in chunks to allow interruption
            for _ in range(1800):  # 30 minutes * 60 seconds
                if self.stop_event.is_set():
                    break
                await asyncio.sleep(1)

        self.is_running = False
        self.status = "Stopped"
        print("[AgentRunner] Agent stopped gracefully.")
