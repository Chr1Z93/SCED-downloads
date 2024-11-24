import json
from pathlib import Path

# Configuration
INPUT_DIR = "./"
EXCLUDE_DIRS = ["./decomposed"]


def minify_json_files(directory, exclude_dirs=None):
    exclude_dirs = set(Path(exclude).resolve() for exclude in (exclude_dirs or []))
    directory_path = Path(directory).resolve()

    if not directory_path.exists():
        print(f"Directory does not exist: {directory}")
        return

    for json_file in directory_path.rglob("*.json"):
        if any(exclude in json_file.parents for exclude in exclude_dirs):
            continue

        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(data, f, separators=(",", ":"), ensure_ascii=False)
            print(f"Minified: {json_file}")
        except json.JSONDecodeError:
            print(f"Error: {json_file} contains invalid JSON.")
        except Exception as e:
            print(f"Error processing {json_file}: {e}")


if __name__ == "__main__":
    minify_json_files(INPUT_DIR, EXCLUDE_DIRS)
