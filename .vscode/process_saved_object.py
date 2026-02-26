import argparse
import json
import os
import platform
import re
import subprocess
import sys
import tempfile
from pathlib import Path

PLATFORM = platform.system()

# --- Helper Functions ---


def read_json_value(file_path, key):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get(key, "")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading JSON file: {e}", file=sys.stderr)
        return ""


def get_saved_objects_dir():
    home = Path.home()
    if PLATFORM == "Windows":
        return (
            home
            / "Documents"
            / "My Games"
            / "Tabletop Simulator"
            / "Saves"
            / "Saved Objects"
        )
    else:  # macOS / Darwin
        return home / "Library" / "Tabletop Simulator" / "Saves" / "Saved Objects"


def get_base_command(script_dir):
    binary_map = {
        "Windows": "TTSModManager.exe",
        "Darwin": "TTSModManager-macOS",
        "Linux": "TTSModManager",
    }
    binary_name = binary_map.get(PLATFORM, "TTSModManager")
    binary_path = script_dir / "bin" / binary_name

    if binary_path.is_file():
        return [str(binary_path)], False
    return ["go", "run", "main.go"], True


def validate_and_prepare_json(input_file):
    """
    Checks if the JSON has the TTS Saved Object wrapper.
    If so, extracts the inner ObjectStates for the TTS Mod Manager.
    """
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict) and "ObjectStates" in data:
            # Extract content via string manipulation to preserve formatting/precision
            with open(input_file, "r", encoding="utf-8") as f:
                content = f.read()

            start_marker = '"ObjectStates": ['
            end_marker = "]\n}"

            start_idx = content.find(start_marker)
            end_idx = content.rfind(end_marker)

            if start_idx != -1 and end_idx != -1:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
                objectstates_content = content[start_idx + len(start_marker) : end_idx]
                with open(temp_file.name, "w", encoding="utf-8") as out_f:
                    out_f.write(objectstates_content)
                return temp_file.name

        return input_file
    except Exception as e:
        print(f"Error validating JSON: {e}", file=sys.stderr)
        return None



# --- Main Logic ---


def main():
    parser = argparse.ArgumentParser(description="Build or Decompose TTS Saved Objects")
    parser.add_argument("--action", required=True, choices=["build", "decompose"])
    parser.add_argument(
        "--input",
        required=True,
        help="The input JSON file (the object source or the TTS saved object)",
    )

    args = parser.parse_args()
    input_path = Path(args.input).resolve()

    # Get Nickname for path construction
    nickname = read_json_value(input_path, "Nickname")
    if not nickname:
        print("Error: Could not read Nickname from input file", file=sys.stderr)
        return

    # Determine Paths
    saved_objects_dir = get_saved_objects_dir()

    # Handle filename sanitization for decomposition lookups
    primary_save_path = saved_objects_dir / f"{nickname}.json"
    sanitized_nickname = re.sub(r"[^\w\s]", "", nickname).strip()
    alt_save_path = saved_objects_dir / f"{sanitized_nickname}.json"

    # Build Command
    script_dir = Path(__file__).resolve().parent
    cmd, using_go = get_base_command(script_dir)

    # Setup SCED paths
    moddir = str(script_dir.parent.parent / "SCED")
    bonusdir = str(script_dir.parent)

    # Run the command
    full_cmd = cmd + ["-moddir", moddir]
    temp_to_clean = None

    if args.action == "build":
        output_file = saved_objects_dir / f"{nickname}.json"
        full_cmd += [
            "-bonusdir",
            bonusdir,
            "-objin",
            str(input_path),
            "-objout",
            str(output_file),
            "-savedobj",
        ]

    else:  # decompose
        # Determine which file actually exists in Saved Objects
        if primary_save_path.exists():
            actual_source = primary_save_path
        elif alt_save_path.exists():
            print(f"Using sanitized path: {alt_save_path}")
            actual_source = alt_save_path
        else:
            print(
                f"Error: Could not find saved object for '{nickname}'", file=sys.stderr
            )
            return

        prepared_source = validate_and_prepare_json(actual_source)
        if prepared_source != str(actual_source):
            temp_to_clean = prepared_source

        full_cmd += [
            "-objin",
            str(prepared_source),
            "-objout",
            str(input_path.parent),
            "-reverse",
        ]

    # Execute
    print(f"Action: {args.action}")
    print(f"Running: {' '.join(full_cmd)}")

    try:
        if using_go:
            # Locate TTSModManager source directory (assumed in same root folder)
            cwd = str(script_dir.parent.parent / "TTSModManager")
            subprocess.run(full_cmd, check=True, cwd=cwd)
        else:
            subprocess.run(full_cmd, check=True)
    finally:
        if temp_to_clean and os.path.exists(temp_to_clean):
            os.remove(temp_to_clean)


if __name__ == "__main__":
    main()
