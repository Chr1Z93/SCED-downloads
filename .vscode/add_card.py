import json
import os
import sys
from pathlib import Path

BASE_PATH_IDENTIFIER = "SCED-downloads"


def get_path_at_depth(full_path, depth_to_skip):
    """
    Finds the base path by searching for target_folder_name,
    then returns the path at the specified depth.
    """

    p = Path(full_path)
    base_path = None

    # Search upwards through parents to find the target folder
    # We check the folder itself (p) and all its parents
    for parent in [p] + list(p.parents):
        if parent.name == BASE_PATH_IDENTIFIER:
            base_path = parent
            break

    if not base_path:
        return f"Error: '{BASE_PATH_IDENTIFIER}' not found in path."

    try:
        # Get relative path from the found base
        relative = p.relative_to(base_path)

        # Slice the parts to skip the requested depth
        remaining_parts = relative.parts[depth_to_skip:]

        # Return as a POSIX string (forward slashes)
        return Path(*remaining_parts).as_posix()

    except (ValueError, IndexError):
        return "Error: Depth to skip exceeds available path length."


def construct_card_json(card_id, nickname, gmnotes_path):
    return {
        "CardID": card_id + "00",
        "CustomDeck": {
            card_id: {
                "BackIsHidden": True,
                "BackURL": "https://steamusercontent-a.akamaihd.net/ugc/2342503777940352139/A2D42E7E5C43D045D72CE5CFC907E4F886C8C690/",
                "FaceURL": "",
                "NumHeight": 1,
                "NumWidth": 1,
                "Type": 0,
                "UniqueBack": False,
            }
        },
        "GMNotes_path": str(get_path_at_depth(gmnotes_path, 3)),
        "GUID": card_id,
        "Name": "Card",
        "Nickname": nickname,
        "Tags": ["Asset", "PlayerCard"],
        "Transform": {"rotY": 270, "scaleX": 1, "scaleY": 1, "scaleZ": 1},
    }


def construct_card_gmnotes(card_id, card_level):
    return {
        "id": card_id,
        "type": "Asset",
        "slot": "Ally",
        "class": "Rogue",
        "level": int(card_level),
        "traits": "",
        "cycle": "Core 2026",
    }


def save_file(data, file_path):
    if os.path.exists(file_path):
        print(f"Error: File already exists at this location.")
        sys.exit(1)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def add_card(active_file_path, card_title, card_level, card_id):
    folder_path = os.path.dirname(active_file_path)

    if card_level != "0":
        nickname = card_title + " (" + card_level + ")"
        base_file_name = card_title + card_level + "." + card_id
    else:
        nickname = card_title
        base_file_name = card_title + "." + card_id

    # Construct the file paths
    json_path = os.path.join(folder_path, f"{base_file_name}.json")
    gmnotes_path = os.path.join(folder_path, f"{base_file_name}.gmnotes")

    # Define the Tabletop Simulator data structures
    json_data = construct_card_json(card_id, nickname, gmnotes_path)
    gmnotes_data = construct_card_gmnotes(card_id, card_level)

    # Write the files
    save_file(json_data, json_path)
    save_file(gmnotes_data, gmnotes_path)

    # Update contained objects of parent file
    parent_file_path = folder_path + ".json"

    if os.path.exists(parent_file_path):
        try:
            with open(parent_file_path, "r", encoding="utf-8") as f:
                parent_data = json.load(f)

            # Ensure the key exists
            if "ContainedObjects_order" not in parent_data:
                parent_data["ContainedObjects_order"] = []

            # Add to the start of the list if it's not already there
            if base_file_name not in parent_data["ContainedObjects_order"]:
                parent_data["ContainedObjects_order"].insert(0, base_file_name)

            # Save the updated parent file
            with open(parent_file_path, "w", encoding="utf-8") as f:
                json.dump(parent_data, f, indent=2)
                f.write("\n")

        except Exception as e:
            print(f"Failed to update parent JSON: {e}")
    else:
        print(f"Warning: Parent file {parent_file_path} not found.")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print(f"Expected 3 arguments, got {len(sys.argv)-1}.")
        print("Use the VS Code task to execute this script.")
        sys.exit(1)

    add_card(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
