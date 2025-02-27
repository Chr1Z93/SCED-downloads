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


def build_saved_object(input_file):
    # Get the nickname
    nickname = read_json_value(input_file, "Nickname")
    if not nickname:
        print("Error: Could not read Nickname from file", file=sys.stderr)
        return

    # Construct output path
    if sys.platform == "darwin": # macOS
        output_file = os.path.join(
            os.path.expanduser("~"),
            "Library",
        )
    else: # windows
        output_file = os.path.join(
            os.environ["USERPROFILE"],
            "Documents",
            "My Games",
        )
    output_file = os.path.join(
        f"{output_file}",
        "Tabletop Simulator",
        "Saves",
        "Saved Objects",
        f"{nickname}.json",
    )

    # Run the go command
    if sys.platform == "darwin": # macOS
        bonusdir_path = os.path.dirname(os.path.dirname(__file__))
        moddir_path = os.path.join(os.path.dirname(bonusdir_path), "SCED")
        cmd = [
            "go",
            "run",
            "main.go",
            "-moddir",
            f"{moddir_path}",
            "-bonusdir",
            f"{bonusdir_path}",
            "-objin",
            f"{input_file}",
            "-objout",
            f"{output_file}",
            "-savedobj",
        ]
    else: # windows
        cmd = [
            "go",
            "run",
            "main.go",
            "--moddir=C:\\git\\SCED",
            "--bonusdir=C:\\git\\SCED-downloads",
            f"--objin={input_file}",
            f"--objout={output_file}",
            "--savedobj",
        ]
    
    # Execute from the correct directory
    if sys.platform == "darwin": # macOS
        modManager_path = os.path.join(os.path.dirname(bonusdir_path), "TTSModManager")
        subprocess.run(cmd, cwd=f"{modManager_path}")
    else: # windows
        subprocess.run(cmd, cwd="C:\\git\\TTSModManager")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python build_saved_object.py <input_file>", file=sys.stderr)
        sys.exit(1)

    build_saved_object(sys.argv[1])
