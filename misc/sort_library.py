import json
import os

# --- Configuration ---

# Define the name of your JSON file
JSON_FILE = "library.json"

# Define the author whose items will be moved to the top, preserving original order
PRIORITY_AUTHOR = "Fantasy Flight Games"

# Define the desired order of keys in the final JSON
KEY_ORDER = [
    "name",
    "type",
    "author",
    "scenariocount",
    "decomposed",
    "cycle_code",
    "filename",
    "boxsize",
    "boxart",
    "description",
]

# Define the sorting order for the 'type' field for non-priority items
TYPE_ORDER = {"playercards": 0, "campaign": 1, "scenario": 2}

# --- Main Script ---


def get_sort_keys(enumerated_item):
    """
    Generates the sorting keys for an item that has been enumerated.
    The input is a tuple: (original_index, item_dictionary).

    - If author is PRIORITY_AUTHOR, items are grouped first and sorted by original index.
    - Otherwise, items are grouped second and sorted by type, then name.
    """
    original_index, item = enumerated_item

    is_priority_author = item.get("author") == PRIORITY_AUTHOR

    if is_priority_author:
        # Group priority items first (key=0), then sort by their original file position.
        # The third element in the tuple is a placeholder and won't be used for these items.
        return (0, original_index, None)
    else:
        # Group all other items second (key=1).
        # Then sort them by type. Finally, sort them by name.
        type_sort = TYPE_ORDER.get(item.get("type"), 99)

        name = item.get("name", "").lower()

        # Special handling for "(Unofficial)"
        if name.startswith("(unofficial) "):
            name = name[13:]

        # Special handling for "'"
        if name.startswith("'"):
            name = name[1:]

        # Special handling for "The"
        if name.startswith("the "):
            name = name[4:]

        return (1, type_sort, name)


def reorder_item_keys(item):
    """
    Reorders the keys in a single dictionary item based on KEY_ORDER.
    """
    ordered_item = {key: item[key] for key in KEY_ORDER if key in item}
    for key, value in item.items():
        if key not in ordered_item:
            ordered_item[key] = value
    return ordered_item


def sort_json_file():
    """
    Main function to read, sort, and write the library.
    """
    if not os.path.exists(JSON_FILE):
        print(f"❌ Library not found in the current directory.")
        return

    try:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        content_list = data.get("content")
        if content_list is None:
            print("❌ 'content' key not found in the library.")
            return

        # Use enumerate to get the original index of each item.
        # This is crucial for preserving the order of priority items.
        enumerated_list = list(enumerate(content_list))

        # Sort the enumerated list using the custom sort key function
        enumerated_list.sort(key=get_sort_keys)

        # Extract the sorted items from the now-sorted enumerated list
        sorted_list = [item for index, item in enumerated_list]

        # Reorder the keys within each item
        final_list = [reorder_item_keys(item) for item in sorted_list]

        data["content"] = final_list

        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")  # Add a newline character at the end

        print(f"✅ Library has been sorted.")

    except json.JSONDecodeError:
        print(f"❌ Could not decode JSON from library. Check for syntax errors.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


# --- Run the script ---
if __name__ == "__main__":
    sort_json_file()
