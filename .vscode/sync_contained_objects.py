# This script rebuilds the ContainedObjects-order key in a JSON file
# and all nested JSON objects in its accompanying folders.

import json
from pathlib import Path
import sys
from typing import List, Dict, Any


def get_contained_file_names(folder_path: Path) -> List[str]:
    """
    Lists all JSON files directly within the given folder,
    stripping their file extensions.

    The list is sorted in reverse alphabetical order.
    """

    # Check if the folder exists and is a directory
    if not folder_path.is_dir():
        print(f"  Warning: Associated folder not found: {folder_path}")
        return []

    file_names = []

    # Iterate over all items in the directory
    for item in folder_path.iterdir():
        if item.is_file() and item.suffix.lower() == ".json":
            file_names.append(item.stem)

    # Sort the list in reverse alphabetical order
    file_names.sort(reverse=True)
    return file_names


def process_json_contained_objects(json_file_path: Path):
    """
    Processes a JSON file and recursively processes all JSON files
    contained in its associated folder hierarchy.
    """

    # Determine the associated folder path
    # The folder name is the JSON filename without the final extension (.json)
    # e.g., 'DerPfadnachCarcosa.6ad5dd.json' -> 'DerPfadnachCarcosa.6ad5dd'
    associated_folder_path = json_file_path.parent / json_file_path.stem

    if not associated_folder_path.exists():
        return

    print(f"  Looking for contained objects in: {associated_folder_path}")

    # Get direct children only
    contained_objects_list = get_contained_file_names(associated_folder_path)

    # Parse the JSON file
    with json_file_path.open("r", encoding="utf-8") as f:
        data: Dict[str, Any] = json.load(f)

    # Update the 'ContainedObjects_order' key
    data["ContainedObjects_order"] = contained_objects_list

    # Save the file: keys sorted alphabetically and ending with a newline
    with json_file_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")

    print(f"    Updated 'ContainedObjects_order' ({len(contained_objects_list)} objects).")

    # Recursively process nested JSON files.
    if associated_folder_path.is_dir():
        for nested_json_path in sorted(
            associated_folder_path.rglob("*.json"),
            key=lambda path: str(path).lower(),
        ):
            process_json_contained_objects(nested_json_path)


if __name__ == "__main__":
    # Get the path passed from VS Code
    if len(sys.argv) < 2:
        print("No path provided.")
        sys.exit(1)

    target_path = Path(sys.argv[1])

    if target_path.is_file() and target_path.suffix.lower() == ".json":
        print("Single file detected.")
        process_json_contained_objects(target_path)

    elif target_path.is_dir():
        print("Folder detected. Checking contents...")

        for entry in target_path.iterdir():
            if entry.is_file() and entry.suffix.lower() == ".json":
                process_json_contained_objects(entry)

    else:
        print("Error: Path is invalid.")
