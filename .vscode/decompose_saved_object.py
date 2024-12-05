import json
import sys
import os
import subprocess


def read_json_value(file_path, key):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get(key, "")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading JSON file: {e}", file=sys.stderr)
        return ""


def decompose_saved_object(input_file):
    # Get the nickname
    nickname = read_json_value(input_file, "Nickname")
    if not nickname:
        print("Error: Could not read Nickname from file", file=sys.stderr)
        return

    # Construct the saved object path
    saved_object = os.path.join(
        os.environ["USERPROFILE"],
        "Documents",
        "My Games",
        "Tabletop Simulator",
        "Saves",
        "Saved Objects",
        f"{nickname}.json",
    )

    # Construct the output path
    output_path = os.path.dirname(input_file)

    # Run the go command
    cmd = [
        "go",
        "run",
        "main.go",
        "--moddir=C:\\git\\SCED",
        f"--objin={saved_object}",
        f"--objout={output_path}\\",
        "--reverse",
    ]

    # Execute from the correct directory
    subprocess.run(cmd, cwd="C:\\git\\TTSModManager")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python decompose_saved_object.py <input_file>", file=sys.stderr)
        sys.exit(1)

    decompose_saved_object(sys.argv[1])
