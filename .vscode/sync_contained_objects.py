# This script rebuilds the ContainedObjects-order key in a JSON file from the accompanying folder.

import json
import os
from pathlib import Path
import sys
from typing import List, Dict, Any


def get_contained_file_names(folder_path: Path) -> List[str]:
    """
    Lists all json files within the given folder, stripping their file extensions.
    The list is sorted alphabetically.
    """
    file_names = []

    # Check if the folder exists and is a directory
    if not folder_path.is_dir():
        print(f"Warning: Associated folder not found. Returning empty list.")
        return []

    # Iterate over all items in the directory
    for item in folder_path.iterdir():
        if item.is_file() and item.suffix == ".json":
            file_names.append(item.stem)

    # Sort the list in reverse alphabetical order
    file_names.sort(reverse=True)
    return file_names


def process_json_contained_objects(json_file_path: str):
    """
    Parses the main JSON file, determines the associated folder, lists and sorts
    the contained files, updates the 'ContainedObjects_order' key, and saves the
    updated JSON file with alphabetically sorted keys and a trailing newline.
    """
    print(f"Starting process for: {json_file_path}")
    main_json_path = Path(json_file_path)

    # Check if the main JSON file exists
    if not main_json_path.exists():
        print(f"Error: Main JSON file not found at {json_file_path}")
        return

    # Determine the associated folder path
    # The folder name is the JSON filename without the final extension (.json)
    # e.g., 'DerPfadnachCarcosa.6ad5dd.json' -> 'DerPfadnachCarcosa.6ad5dd'
    folder_name = main_json_path.stem
    associated_folder_path = main_json_path.parent / folder_name
    print(f"Looking for contained objects in folder: {associated_folder_path}")

    # Get the list of file names from the associated folder
    contained_objects_list = get_contained_file_names(associated_folder_path)
    print(f"Found {len(contained_objects_list)} json files.")

    # Parse the JSON file
    with open(main_json_path, "r", encoding="utf-8") as f:
        data: Dict[str, Any] = json.load(f)

    # Update the 'ContainedObjects_order' key
    data["ContainedObjects_order"] = contained_objects_list

    # Save the file: keys sorted alphabetically and ending with a newline
    with open(main_json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")

    print(f"Updated 'ContainedObjects_order' in {json_file_path}")


if __name__ == "__main__":
    # Get the path passed from VS Code
    if len(sys.argv) < 2:
        print("No path provided.")
        sys.exit(1)

    target_path = sys.argv[1]

    if os.path.isfile(target_path) and target_path.lower().endswith(".json"):
        print(f"Single file detected.")
        process_json_contained_objects(target_path)
    elif os.path.isdir(target_path):
        print(f"Folder detected. Checking contents...")
        for entry in os.listdir(target_path):
            full_path = os.path.join(target_path, entry)
            if os.path.isfile(full_path) and full_path.lower().endswith(".json"):
                process_json_contained_objects(full_path)
    else:
        print(f"Error: Path is invalid.")
