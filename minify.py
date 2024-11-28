import json
from pathlib import Path

# Configuration: List of directories and files to process
INPUT_DIRS = ["./.build", "./downloadable"]
INPUT_FILES = ["./modversion.json", "./library.json"]


def minify_json_file(json_file):
    try:
        json_file_path = Path(json_file).resolve()
        if not json_file_path.exists():
            print(f"File does not exist: {json_file}")
            return

        with open(json_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, separators=(",", ":"), ensure_ascii=False)

        # print(f"Minified: {json_file}")
    except json.JSONDecodeError:
        print(f"Error: {json_file} contains invalid JSON.")
    except Exception as e:
        print(f"Error processing {json_file}: {e}")


if __name__ == "__main__":
    # Process input directories and contained files
    for directory in INPUT_DIRS:
        directory_path = Path(directory).resolve()
        if not directory_path.exists():
            print(f"Directory does not exist: {directory}")
            continue

        # print(f"Processing directory: {directory}")
        for json_file in directory_path.rglob("*.json"):
            minify_json_file(json_file)

    # Process input files
    for json_file in INPUT_FILES:
        minify_json_file(json_file)
