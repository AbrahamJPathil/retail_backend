import asyncio
from pathlib import Path
from typing import Any, Dict, List

from app.storage.json_manager import read_json, write_json

DATA_DIR = Path("data")


def _next_numeric_id(items: List[Dict[str, Any]]) -> int:
    numeric_ids = [item.get("id") for item in items if isinstance(item.get("id"), int)]
    return (max(numeric_ids) + 1) if numeric_ids else 1


def _make_test_record(file_path: Path, next_id: int) -> Dict[str, Any]:
    return {
        "id": next_id,
        "__test_marker": "json_manager_crud",
        "file": file_path.name,
        "value": "created-by-test-script",
    }


async def _run_crud_for_file(file_path: Path) -> None:
    file_str = str(file_path)
    print(f"\n--- Testing {file_str} ---")

    # Read
    original_data = await read_json(file_str)
    if not isinstance(original_data, list):
        raise AssertionError(f"Expected list in {file_str}, got {type(original_data)}")
    print(f"READ: loaded {len(original_data)} records")

    # Create
    created_record = _make_test_record(file_path, _next_numeric_id(original_data))
    created_data = original_data + [created_record]
    await write_json(file_str, created_data)

    after_create = await read_json(file_str)
    if len(after_create) != len(original_data) + 1:
        raise AssertionError(f"CREATE failed for {file_str}: record count mismatch")
    created_index = next(
        (idx for idx, row in enumerate(after_create) if row.get("__test_marker") == "json_manager_crud"),
        -1,
    )
    if created_index == -1:
        raise AssertionError(f"CREATE failed for {file_str}: test record not found")
    print("CREATE: appended one test record")

    # Update
    after_create[created_index]["value"] = "updated-by-test-script"
    await write_json(file_str, after_create)

    after_update = await read_json(file_str)
    updated_row = next(
        (row for row in after_update if row.get("__test_marker") == "json_manager_crud"),
        None,
    )
    if not updated_row or updated_row.get("value") != "updated-by-test-script":
        raise AssertionError(f"UPDATE failed for {file_str}: value not updated")
    print("UPDATE: modified test record")

    # Delete
    after_delete = [row for row in after_update if row.get("__test_marker") != "json_manager_crud"]
    await write_json(file_str, after_delete)

    final_data = await read_json(file_str)
    if len(final_data) != len(original_data):
        raise AssertionError(f"DELETE failed for {file_str}: record count mismatch")
    if any(row.get("__test_marker") == "json_manager_crud" for row in final_data):
        raise AssertionError(f"DELETE failed for {file_str}: test record still present")
    print("DELETE: removed test record")


async def main() -> None:
    data_files = sorted(DATA_DIR.glob("*.json"))
    if not data_files:
        raise FileNotFoundError("No JSON files found under data/")

    print("Starting JSON Manager CRUD tests")
    print(f"Found {len(data_files)} JSON files in data/")

    # Keep full backup so we can restore exact baseline after tests.
    backups: Dict[str, List[Dict[str, Any]]] = {}
    for file_path in data_files:
        backups[str(file_path)] = await read_json(str(file_path))

    try:
        for file_path in data_files:
            await _run_crud_for_file(file_path)
        print("\nAll CRUD tests passed")
    finally:
        for file_name, original_data in backups.items():
            await write_json(file_name, original_data)
        print("Restored original contents for all tested files")


if __name__ == "__main__":
    asyncio.run(main())
