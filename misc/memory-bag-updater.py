import json
from pathlib import Path
import re

# --- CONFIGURATION ---
SCRIPT_DIR = Path(__file__).resolve().parent
INPUT_DIR = SCRIPT_DIR.parent / "downloadable"
SEARCH_TEXT = "-- Utility memory bag by Directsun"
SEARCH_TEXT_2 = 'tooltip = "Update memory for placed objects",'

# We go up twice to the 'git' folder, then down into 'SCED'
MB_SCRIPT_FILE = SCRIPT_DIR.parents[1] / "SCED" / "src" / "MemoryBag.ttslua"
MB_WRAPPER_FILE = SCRIPT_DIR / "memory-bag-template.ttslua"


class TTSUpdater:
    def __init__(self, search_text, search_text_2, script_path, wrapper_path):
        self.search_text = search_text
        self.search_text_2 = search_text_2

        # Generate the full Lua string once at the start
        script_content = self.clean_lua(script_path.read_text(encoding="utf-8"))
        self.replacement_content = self.clean_lua(
            wrapper_path.read_text(encoding="utf-8")
        ).replace("--<<PLACEHOLDER>>", script_content)

    def clean_lua(self, text):
        # Remove tabs
        text = text.replace("\t", "")

        # Use regex to remove leading whitespace from every line
        return re.sub(r"^[ ]+", "", text, flags=re.MULTILINE)

    def process_node(self, node, parent=None):
        """Recursively searches for 'LuaScript' keys and updates parent's LuaScriptState."""
        changed = False

        if isinstance(node, dict):
            # Check if this specific dictionary is a matching TTS object
            if "LuaScript" in node and isinstance(node["LuaScript"], str):
                if (
                    self.search_text in node["LuaScript"]
                    or self.search_text_2 in node["LuaScript"]
                ):
                    # Update the script content
                    node["LuaScript"] = self.replacement_content
                    changed = True

                    # Update the Transform if it exists
                    if "Transform" in node and isinstance(node["Transform"], dict):
                        # Ensure rotY is set to 270
                        node["Transform"]["rotY"] = 270

                    # Update the PARENT'S LuaScriptState if applicable
                    guid = node.get("GUID")
                    if parent and guid and "LuaScriptState" in parent:
                        try:
                            state_data = json.loads(parent["LuaScriptState"])

                            # Check if our GUID exists in the state (e.g., memory bag storage)
                            if (
                                "ml" in state_data
                                and guid in state_data["ml"]
                                and "rot" in state_data["ml"][guid]
                            ):
                                state_data["ml"][guid]["rot"]["y"] = 270
                                # Save it back as a stringified JSON
                                parent["LuaScriptState"] = json.dumps(
                                    state_data, separators=(",", ":")
                                )
                        except (json.JSONDecodeError, TypeError):
                            # If it's not valid JSON or not a dict, we skip it
                            pass

            # Continue recursion, passing the current node as the next level's parent
            for value in node.values():
                if self.process_node(value, parent=node):
                    changed = True

        elif isinstance(node, list):
            for item in node:
                # When iterating through a list (like 'ContainedObjects'),
                # the 'parent' remains the dict that holds the list.
                if self.process_node(item, parent=parent):
                    changed = True

        return changed

    def run(self, target_dir):
        if not target_dir.exists():
            print(f"Error: {target_dir} not found.")
            return

        for file_path in target_dir.rglob("*.json"):
            try:
                # Load the JSON object
                data = json.loads(file_path.read_text(encoding="utf-8"))

                if self.process_node(data):
                    print(f"Updating: {file_path.relative_to(target_dir.parent)}")
                    # json.dumps automatically escapes newlines into \n
                    file_path.write_text(
                        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8",
                    )

            except (json.JSONDecodeError, IOError) as e:
                print(f"Skipping {file_path.name} due to error: {e}")


if __name__ == "__main__":
    updater = TTSUpdater(SEARCH_TEXT, SEARCH_TEXT_2, MB_SCRIPT_FILE, MB_WRAPPER_FILE)
    updater.run(INPUT_DIR)
    print("\nProcess complete.")
