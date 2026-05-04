"""
Agent Runner Module
-------------------
Background orchestrator that runs the Scout -> Librarian -> Analyst -> Reporter
pipeline in a continuous loop. Respects AC power state and supports graceful
stop/start via async events.
"""

import asyncio
import time
import traceback
import psutil
from core.scout import gather_all_links
from core.librarian import Librarian
from core.analyst import Analyst
from core.reporter import Reporter


class AgentRunner:
    """Manages the background scraping/analysis loop."""

    def __init__(self):
        self.librarian = Librarian()
        self.analyst = Analyst()
        self.reporter = Reporter()
        self.is_running = False
        self.status = "Stopped"
        # Defer Event creation until start() so we are always on a live loop
        self._stop_event: asyncio.Event | None = None
        self._task: asyncio.Task | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def start(self):
        """Start the background agent. Idempotent — calling twice is safe."""
        if self.is_running:
            return
        self.is_running = True
        self._stop_event = asyncio.Event()
        self.status = "Starting..."
        print("[AgentRunner] Background agent started.")
        # Keep a reference so the task is not garbage-collected
        self._task = asyncio.create_task(self._run_loop())

    async def stop(self):
        """Signal the background agent to stop gracefully."""
        if not self.is_running:
            return
        self.status = "Stopping..."
        if self._stop_event:
            self._stop_event.set()
        print("[AgentRunner] Stop signal sent to background agent.")

    async def get_status(self):
        """Return current agent status and power-plug state."""
        battery = psutil.sensors_battery()
        # Desktop PCs return None for battery — treat as always plugged in
        plugged = battery.power_plugged if battery else True
        return {
            "status": self.status,
            "battery_plugged": plugged,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _should_stop(self) -> bool:
        """Check whether a stop has been requested."""
        return self._stop_event is not None and self._stop_event.is_set()

    async def _process_link(self, link_info: dict):
        """Run a single link through the Librarian -> Analyst -> Reporter pipeline."""
        if self._should_stop():
            return

        url = link_info.get("link", "")
        title = link_info.get("title", "")
        # Safely encode the title for console output
        safe_title = title.encode("ascii", "ignore").decode("ascii") if title else "Unknown Title"
        print(f"\n--- Processing: {safe_title} ---")

        try:
            markdown = await self.librarian.extract_markdown(url)
            if not markdown or self._should_stop():
                return

            analysis_result = await self.analyst.analyze_article(markdown, url)
            if not analysis_result or self._should_stop():
                return

            self.reporter.add_entry(analysis_result)
        except Exception as exc:
            print(f"[AgentRunner] Error processing {url}: {exc}")

    async def _run_loop(self):
        """
        Main loop: scout links, then process each one sequentially.
        Runs for up to 6 hours per session and pauses when on battery.
        """
        start_time = time.time()
        max_runtime = 6 * 3600  # 6 hours

        try:
            while time.time() - start_time < max_runtime:
                if self._should_stop():
                    break

                # ---- Battery guard ----
                battery = psutil.sensors_battery()
                is_plugged = battery.power_plugged if battery else True

                if not is_plugged:
                    self.status = "Paused (On Battery)"
                    print("[AgentRunner] Laptop on battery. Pausing for 1 minute...")
                    await asyncio.sleep(60)
                    continue

                # ---- Phase 1: Scout ----
                self.status = "Running — Scouting"
                print("\n[Phase 1] Scouting for raw links...")
                try:
                    links = await gather_all_links()
                except Exception as exc:
                    print(f"[AgentRunner] Scout phase failed: {exc}")
                    links = []

                # ---- Phase 2: Process ----
                self.status = f"Running — Analysing {len(links)} links"
                print(f"\n[Phase 2] Analysing {len(links)} links...")
                for link_info in links:
                    if self._should_stop():
                        break
                    # Sequential to avoid GPU OOM with local Ollama
                    await self._process_link(link_info)

                if self._should_stop():
                    break

                # ---- Sleep between cycles ----
                self.status = "Sleeping (Next run in 30 mins)"
                print("\n[AgentRunner] Pipeline complete. Sleeping for 30 minutes...")

                # Sleep in 1-second chunks so we can respond to stop quickly
                for _ in range(1800):
                    if self._should_stop():
                        break
                    await asyncio.sleep(1)

        except asyncio.CancelledError:
            print("[AgentRunner] Background task was cancelled.")
        except Exception as exc:
            print(f"[AgentRunner] Unexpected error in run loop:\n{traceback.format_exc()}")
        finally:
            self.is_running = False
            self.status = "Stopped"
            print("[AgentRunner] Agent stopped gracefully.")
