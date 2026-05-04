"""
Reporter Module — Persists analysis results to Excel with dedup.
"""

import pandas as pd
import os
import threading
from datetime import datetime, timezone
from typing import Dict

REPORT_COLUMNS = [
    "Company", "Model", "Metrics", "InnovationSummary",
    "SemanticHash", "SourceURL", "Timestamp",
]


class Reporter:
    """Append-only reporter with in-memory duplicate detection."""

    def __init__(self, output_file: str = "ai_intelligence_report.xlsx"):
        self.output_file = output_file
        self.existing_hashes: set = set()
        self._lock = threading.Lock()
        self._load_existing_data()

    def _load_existing_data(self):
        if os.path.exists(self.output_file):
            try:
                df = pd.read_excel(self.output_file)
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
                print(f"[Reporter] Duplicate. Skipping: {data.get('Model')}")
                return False
            self.existing_hashes.add(semantic_hash)

            new_row = {
                "Company": data.get("Company", ""),
                "Model": data.get("Model", ""),
                "Metrics": data.get("Metrics", ""),
                "InnovationSummary": data.get("InnovationSummary", ""),
                "SemanticHash": data.get("SemanticHash", ""),
                "SourceURL": data.get("SourceURL", ""),
                "Timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            }
            try:
                if os.path.exists(self.output_file):
                    df = pd.read_excel(self.output_file)
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                else:
                    df = pd.DataFrame([new_row], columns=REPORT_COLUMNS)
                df.to_excel(self.output_file, index=False)
                print(f"[Reporter] Added: {data.get('Model')}")
                return True
            except PermissionError:
                print(f"[Reporter] File locked — close Excel and retry.")
                self.existing_hashes.discard(semantic_hash)
                return False
            except Exception as exc:
                print(f"[Reporter] Error saving: {exc}")
                self.existing_hashes.discard(semantic_hash)
                return False
