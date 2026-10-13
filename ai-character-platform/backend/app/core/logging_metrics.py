import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from app.core.config import settings

LOG_FILE = Path(settings.METRICS_LOG_PATH)

def log_metric(data: Dict[str, Any]) -> None:
    """Safely append a metric record to the JSONL log file."""
    try:
        default_source = "benchmark" if os.getenv("BENCHMARK_MODE") == "1" else "website"
        record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "source": data.get("source", default_source),
            **data
        }
        if "source" not in data:
            record["source"] = default_source
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except Exception as e:
        # Never crash request flow on metric logging failure
        print(f"[METRICS_LOG_ERROR] {e}")
