import json
from pathlib import Path

OUTPUT_DIR = "./.build"

def minify_json_files(directory):
    directory_path = Path(directory)
    for json_file in directory_path.glob("*.json"):
        with open(json_file, "r") as f:
            data = json.load(f)

        with open(json_file, "w") as f:
            json.dump(data, f, separators=(",", ":"))

if __name__ == "__main__":
    minify_json_files(OUTPUT_DIR)
