import json
import logging
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

# backend/app/data/guidelines.py -> backend/data/maintenance_guidelines.json
GUIDELINES_FILE = (
    Path(__file__).resolve().parent.parent.parent
    / "data"
    / "maintenance_guidelines.json"
)


@lru_cache(maxsize=1)
def load_guidelines() -> list[dict]:
    """
    Load maintenance guidelines from JSON file.
    Cached in memory with lru_cache — file read happens
    once at first call, subsequent calls return the cached list.
    No DB, no Redis needed for loading — file is in the repo.
    Redis is still used for rate limiting protection.
    """
    try:
        with open(GUIDELINES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            logger.debug("Loaded %d maintenance guidelines from file", len(data))
            return data
    except FileNotFoundError:
        logger.error("Guidelines file not found at %s", GUIDELINES_FILE)
        return []
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON in guidelines file: %s", e)
        return []
