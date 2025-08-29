import os
import json

OVERRIDE_PATH = "overrides/override_log.jsonl"
os.makedirs("overrides", exist_ok=True)

def log_override(document_id, original, corrected):
    entry = {
        "document_id": document_id,
        "original_classification": original,
        "corrected_classification": corrected
    }
    with open(OVERRIDE_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")
