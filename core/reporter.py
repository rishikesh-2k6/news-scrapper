import pandas as pd
import os
from typing import Dict

class Reporter:
    def __init__(self, output_file: str = "ai_intelligence_report.xlsx"):
        self.output_file = output_file
        self.existing_hashes = set()
        self._load_existing_data()

    def _load_existing_data(self):
        if os.path.exists(self.output_file):
            try:
                df = pd.read_excel(self.output_file)
                if "SemanticHash" in df.columns:
                    # Load existing hashes to prevent duplicates
                    self.existing_hashes = set(df["SemanticHash"].dropna().str.lower().tolist())
                print(f"[Reporter] Loaded existing report with {len(self.existing_hashes)} entries.")
            except Exception as e:
                print(f"[Reporter] Error loading existing report: {e}")
        else:
            print("[Reporter] No existing report found. Will create a new one.")

    def add_entry(self, data: Dict) -> bool:
        """
        Appends a new entry if it doesn't already exist.
        Returns True if added, False if duplicate or invalid.
        """
        if not data:
            return False

        semantic_hash = data.get("SemanticHash", "").strip().lower()
        if not semantic_hash:
            return False

        if semantic_hash in self.existing_hashes:
            print(f"[Reporter] Duplicate detected. Skipping entry for: {data.get('Model')}")
            return False

        # Add to current memory
        self.existing_hashes.add(semantic_hash)

        # Prepare row
        new_row = {
            "Company": data.get("Company", ""),
            "Model": data.get("Model", ""),
            "Metrics": data.get("Metrics", ""),
            "InnovationSummary": data.get("InnovationSummary", ""),
            "SemanticHash": data.get("SemanticHash", ""),
            "SourceURL": data.get("SourceURL", "")
        }

        try:
            if os.path.exists(self.output_file):
                df = pd.read_excel(self.output_file)
                # Use pd.concat instead of append (deprecated in newer pandas)
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            else:
                df = pd.DataFrame([new_row])

            df.to_excel(self.output_file, index=False)
            print(f"[Reporter] Successfully added new entry to report: {data.get('Model')}")
            return True
        except Exception as e:
            print(f"[Reporter] Error saving to Excel: {e}")
            return False
