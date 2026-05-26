import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any

# Global dictionary to maintain a unique lock for every individual file.
# This ensures reading/writing to 'products.json' doesn't block 'customers.json'.
_FILE_LOCKS: Dict[str, asyncio.Lock] = {}

def _get_lock_for_file(file_path: str) -> asyncio.Lock:
    """Retrieves or creates a thread-safe async lock for a specific file path."""
    if file_path not in _FILE_LOCKS:
        _FILE_LOCKS[file_path] = asyncio.Lock()
    return _FILE_LOCKS[file_path]


def _initialize_file(file_path: str) -> None:
    """Ensures the data file and its parent directories exist with an empty JSON array."""
    path = Path(file_path)
    
    # 1. Create parent directories if they don't exist
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # 2. If file doesn't exist or is empty, initialize it with a clean JSON array '[]'
    if not path.exists() or path.stat().st_size == 0:
        with open(path, "w", encoding="utf-8") as f:
            json.dump([], f)


async def read_json(file_path: str) -> List[Dict[str, Any]]:
    """
    Safely reads and parses a JSON file.
    Acquires a lock to ensure we don't read a file while it's mid-write.
    """
    _initialize_file(file_path)
    lock = _get_lock_for_file(file_path)
    
    async with lock:
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []  # Fallback recovery if JSON gets malformed


async def write_json(file_path: str, data: List[Dict[str, Any]]) -> None:
    """
    Safely overwrites a JSON file with updated data.
    Acquires an exclusive lock to prevent data overlapping/corruption.
    """
    _initialize_file(file_path)
    lock = _get_lock_for_file(file_path)
    
    async with lock:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)