"""
Reporter Module — Persists analysis results to CSV with dedup.
"""

import pandas as pd
import os
import threading
from datetime import datetime, timezone
from typing import Dict

REPORT_COLUMNS = [
    "company", "name", "category", "impact_score",
    "innovation", "use_case", "technical_depth", "benchmark",
    "hook", "explanation", "why_it_matters", "content_idea",
    "SemanticHash", "SourceURL", "Timestamp",
]


class Reporter:
    """Append-only reporter with in-memory duplicate detection."""

    def __init__(self, output_file: str = "ai_intelligence_report.csv"):
        self.output_file = output_file
        self.existing_hashes: set = set()
        self._lock = threading.Lock()
        self._load_existing_data()

    def _load_existing_data(self):
        if os.path.exists(self.output_file):
            try:
                df = pd.read_csv(self.output_file)
                if "SemanticHash" in df.columns:
                    self.existing_hashes = set(
                        df["SemanticHash"].dropna().astype(str).str.lower().tolist()
                    )
                print(f"[Reporter] Loaded {len(self.existing_hashes)} existing entries.")
            except Exception as exc:
                print(f"[Reporter] Error loading report: {exc}")
        else:
            print("[Reporter] No existing report. Will create a new one.")

    def add_entry(self, data: Dict) -> bool:
        if not data:
            return False
        semantic_hash = str(data.get("SemanticHash", "")).strip().lower()
        if not semantic_hash:
            return False

        with self._lock:
            if semantic_hash in self.existing_hashes:
                print(f"[Reporter] Duplicate. Skipping: {data.get('name')}")
                return False
            self.existing_hashes.add(semantic_hash)

            new_row = {
                "company": data.get("company", ""),
                "name": data.get("name", ""),
                "category": data.get("category", ""),
                "impact_score": data.get("impact_score", ""),
                "innovation": data.get("innovation", ""),
                "use_case": data.get("use_case", ""),
                "technical_depth": data.get("technical_depth", ""),
                "benchmark": data.get("benchmark", "N/A"),
                "hook": data.get("hook", ""),
                "explanation": data.get("explanation", ""),
                "why_it_matters": data.get("why_it_matters", ""),
                "content_idea": data.get("content_idea", ""),
                "SemanticHash": data.get("SemanticHash", ""),
                "SourceURL": data.get("SourceURL", ""),
                "Timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            }
            try:
                if os.path.exists(self.output_file):
                    df = pd.read_csv(self.output_file)
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                else:
                    df = pd.DataFrame([new_row], columns=REPORT_COLUMNS)
                df.to_csv(self.output_file, index=False)
                print(f"[Reporter] Added: {data.get('name')}")
                return True
            except PermissionError:
                print("[Reporter] File locked — close it and retry.")
                self.existing_hashes.discard(semantic_hash)
                return False
            except Exception as exc:
                print(f"[Reporter] Error saving: {exc}")
                self.existing_hashes.discard(semantic_hash)
                return False
