import json
import sys
import os
import subprocess
import tempfile


def read_json_value(file_path, key):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get(key, "")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading JSON file: {e}", file=sys.stderr)
        return ""


def validate_and_prepare_json(input_file):
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Check if the saved object wrapper is present
        if (
            isinstance(data, dict)
            and "GameComplexity" in data
            and isinstance(data["GameComplexity"], str)
            and "ObjectStates" in data
            and isinstance(data["ObjectStates"], list)
        ):
            # Create a temporary file and pass its path to the function
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
            return extract_objectstates_string_edit(input_file, temp_file.name)
        else:
            # Structure is already correct
            return input_file
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error validating JSON structure: {e}", file=sys.stderr)
        return None


def extract_objectstates_string_edit(input_file, output_file):
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Define the start and end parts to remove
        start_marker = '"ObjectStates": ['
        end_marker = "]\n}"  # Assuming the file ends like this

        # Find the start of the ObjectStates array
        start_idx = content.find(start_marker)
        if start_idx == -1:
            print("Error: 'ObjectStates' not found in JSON file.")
            return input_file  # Return original file if ObjectStates is missing

        # Find the end of the array
        end_idx = content.rfind(end_marker)
        if end_idx == -1:
            print("Error: Invalid structure for 'ObjectStates' array.")
            return input_file

        # Extract the content of ObjectStates array
        objectstates_content = content[start_idx + len(start_marker) : end_idx]

        # Write the content to the output file
        with open(output_file, "w", encoding="utf-8") as out_f:
            out_f.write(objectstates_content)

        return output_file
    except Exception as e:
        print(f"Error during string manipulation: {e}")
        return None


def decompose_saved_object(input_file):
    # Get the nickname
    nickname = read_json_value(input_file, "Nickname")
    if not nickname:
        print("Error: Could not read Nickname from file", file=sys.stderr)
        return

    # Construct the saved object path
    if sys.platform == "darwin": # macOS
        saved_object = os.path.join(
            os.path.expanduser("~"),
            "Library",
        )
    else: # windows
        saved_object = os.path.join(
            os.environ["USERPROFILE"],
            "Documents",
            "My Games",
        )
    saved_object = os.path.join(
        f"{saved_object}",
        "Tabletop Simulator",
        "Saves",
        "Saved Objects",
        f"{nickname}.json",
    )

    # Validate and prepare the saved object JSON
    prepared_saved_object = validate_and_prepare_json(saved_object)
    if not prepared_saved_object:
        print("Error: Invalid or corrupted saved object JSON file", file=sys.stderr)
        return

    # Construct the output path
    output_path = os.path.dirname(input_file)

    # Run the go command
    if sys.platform == "darwin": # macOS
        moddir_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "SCED")
        cmd = [
            "go",
            "run",
            "main.go",
            "-moddir",
            f"{moddir_path}",
            "-objin",
            f"{prepared_saved_object}",
            "-objout",
            f"{output_path}",
            "-reverse",
        ]
    else: # windows
        cmd = [
            "go",
            "run",
            "main.go",
            "--moddir=C:\\git\\SCED",
            f"--objin={prepared_saved_object}",
            f"--objout={output_path}\\",
            "--reverse",
        ]

    # Execute from the correct directory
    if sys.platform == "darwin": # macOS
        modManager_path = os.path.join(os.path.dirname(moddir_path), "TTSModManager")
        subprocess.run(cmd, cwd=f"{modManager_path}")
    else: # windows
        subprocess.run(cmd, cwd="C:\\git\\TTSModManager")

    # Clean up temporary file if created
    if prepared_saved_object != saved_object:
        os.remove(prepared_saved_object)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python decompose_saved_object.py <input_file>", file=sys.stderr)
        sys.exit(1)

    decompose_saved_object(sys.argv[1])
