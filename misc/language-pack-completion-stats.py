from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import logging
import json
import os
from pathlib import Path
import re
import time

# ==========================================
# CONFIGURATION
# ==========================================

PLAYER_CARD_PATH_1 = Path(r"C:\git\SCED\objects\AdditionalPlayerCards.2cba6b")
PLAYER_CARD_PATH_2 = Path(r"C:\git\SCED\objects\AllPlayerCards.15bb07")
ROOT_PATH = Path(r"C:\git\SCED-downloads\decomposed")
REPORT_PATH = Path(r"C:\git\SCED-downloads\misc\localization_reports")
EXCLUDED_FOLDERS = {
    "language-pack",
    "misc",
    ".git",
    ".vscode",
    # fan campaigns
    "Ages Unwound",
    "Alice in Wonderland",
    "Bloodborne - City of the Unseen",
    "Call of the Plaguebearer",
    "Celtic Rising",
    "Circus Ex Mortis",
    "Cyclopean Foundations",
    "Dark Matter",
    "Darkham Horror",
    "Night of Vespers",
    "Rise, Rapture, Rise",
    "Starter Decks 2026 - Preview Cards",
    "The Crown of Egil",
    "The Ghosts of Onigawa",
    "Unofficial Return to The Scarlet Keys",
    # fan player cards
    "Baldurs Gate III",
    "Circus Ex Mortis",
    "City of Secrets",
    "Mass Effect Investigators",
    "MythosBusters Campaign Play-Along Cards",
    "Rabbit Hole Expansion",
    "Touhou Project Investigators",
    # fan scenarios
    "Cosmic Pantheon",
    "The Grand Oak Hotel",
    "The Symphony of Erich Zann",
    "The Woods of the Black Goat",
}
NOT_ORPHANS = {
    "LatestFAQ",
    "LearnToPlay",
    "PhaseReference",
    "RoundSequence",
    "RulesReference",
    "89005",  # Reality Acid Sheet
    "98019", # Gloria Goldberg Promo
    "CGWTWS01",  # When The World Screamed scenario guide
}

# Derived Paths
LP_PATH = ROOT_PATH / "language-pack"
SCRIPT_DIR = Path(__file__).parent.absolute()
CACHE_FILE = SCRIPT_DIR / "language-pack-completion-stats_cache.json"

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# ==========================================
# PROCESSING HELPERS
# ==========================================


# This loads the data for player cards
def load_playercard_data(root_folder):
    card_data = {}
    for dirpath, dirs, filenames in os.walk(root_folder):
        current_path = Path(dirpath)

        for filename in filenames:
            if filename.endswith(".json"):
                file_path = current_path / filename

                # Attempt to get ID from external .gmnotes
                gmnotes_file = file_path.with_suffix(".gmnotes")
                if gmnotes_file.exists():
                    with gmnotes_file.open("r", encoding="utf-8") as f:
                        gm_data = json.load(f)
                        found_id = get_id(gm_data)
                        if found_id:
                            card_data[found_id] = gm_data.get("cycle", "Unknown")
                            continue

                # Attempt to get ID from embedded GM Notes
                with file_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)

                gm_notes_raw = data.get("GMNotes", "")
                if gm_notes_raw:
                    gm_data = json.loads(gm_notes_raw)
                    found_id = get_id(gm_data)
                    if found_id:
                        card_data[found_id] = gm_data.get("cycle", "Unknown")

    return card_data


def get_id(gm_data):
    # Skip fanmade content
    if "TtsZoopGuid" in gm_data:
        return None
    return gm_data.get("id")


def process_file(current_path, filename):
    file_path = current_path / filename
    found_id = None

    try:
        # Attempt to get ID from external .gmnotes
        gmnotes_file = file_path.with_suffix(".gmnotes")
        if gmnotes_file.exists():
            with gmnotes_file.open("r", encoding="utf-8") as f:
                gm_data = json.load(f)
                found_id = get_id(gm_data)
                if found_id:
                    return return_with_folder(found_id, file_path.parent)

        # Attempt to get ID from embedded GM Notes
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        gm_notes_raw = data.get("GMNotes", "")
        if gm_notes_raw:
            try:
                gm_data = json.loads(gm_notes_raw)
                found_id = get_id(gm_data)
                if found_id:
                    return return_with_folder(found_id, current_path)
            except (json.JSONDecodeError, TypeError):
                pass

        # Handle ID-less objects (skip bags)
        if "ContainedObjects_order" in data or "ContainedObjects" in data:
            return None

        return None, file_path  # Track missing ID

    except Exception:
        return None


def return_with_folder(found_id, path_obj):
    """Helper to extract main folder."""
    try:
        # Find the index of "decomposed" in the path parts
        parts = path_obj.parts
        idx = parts.index("decomposed")

        # Grab the next two folders and join them
        main_folder = Path(*parts[idx + 1 : idx + 3])
        return found_id, str(main_folder)
    except (ValueError, IndexError):
        return found_id, "Unknown"


# ==========================================
# SCANNING ENGINES
# ==========================================


def generate_id_map():
    id_to_content_map = {}
    files_without_id = []
    tasks = []

    start_time = time.perf_counter()

    # Scanning Phase
    logging.info(f"Starting scan in {ROOT_PATH}")
    with ThreadPoolExecutor(max_workers=8) as executor:
        for dirpath, dirs, filenames in os.walk(ROOT_PATH):
            # This modifies the dirs list in-place, so os.walk won't visit them
            dirs[:] = [
                d
                for d in dirs
                if d not in EXCLUDED_FOLDERS and "Fan Campaigns" not in d
            ]

            current_path = Path(dirpath)

            for filename in filenames:
                if filename.endswith(".json"):
                    tasks.append(executor.submit(process_file, current_path, filename))

        scan_done = time.perf_counter()
        logging.info(
            f"Scan complete. Found {len(tasks)} JSON files in {scan_done - start_time:.2f}s"
        )

        # Processing Phase
        for task in tasks:
            result = task.result()
            if result:
                card_id, data = result
                if card_id is None:  # data is the file path
                    files_without_id.append(data)
                else:  # data is the main folder
                    # skip mini cards
                    if not card_id.endswith("-m"):
                        id_to_content_map[card_id] = data

    processing_time = time.perf_counter()
    logging.info(f"Processing completed in {processing_time - scan_done:.2f}s")

    # Add player card data
    data_1 = load_playercard_data(PLAYER_CARD_PATH_1)
    data_2 = load_playercard_data(PLAYER_CARD_PATH_2)
    player_card_data = data_1 | data_2

    for card_id, cycle in player_card_data.items():
        id_to_content_map[card_id] = "playercards\\" + cycle

    end_time = time.perf_counter()

    logging.info(
        f"Loading player card data from API completed in: {end_time - processing_time:.2f}s"
    )
    logging.info(f"Total time: {end_time - start_time:.2f}s")

    return id_to_content_map, files_without_id


def generate_lang_id_set(lang_root):
    """
    Crawls the language folder and returns a simple set of all found IDs.
    We reuse the 'process_file' logic but ignore the 'main_folder' return.
    """
    found_ids = set()
    files_without_id = []
    tasks = []

    with ThreadPoolExecutor(max_workers=8) as executor:
        for dirpath, dirs, filenames in os.walk(lang_root):
            # Still exclude noise
            dirs[:] = [
                d
                for d in dirs
                if d not in EXCLUDED_FOLDERS and "Fan Campaigns" not in d
            ]

            current_path = Path(dirpath)

            for filename in filenames:
                if filename.endswith(".json"):
                    tasks.append(executor.submit(process_file, current_path, filename))

        for task in tasks:
            result = task.result()
            if result:
                card_id, data = result
                if card_id is None:
                    anchor = "language-pack"

                    # Find the part of the path relative to 'language-pack'
                    if anchor in data.parts:
                        relative_path = data.relative_to(
                            Path(dirpath[: dirpath.find(anchor) + len(anchor)])
                        )
                        files_without_id.append(str(relative_path))
                else:
                    found_ids.add(card_id)

    return found_ids, files_without_id


# ==========================================
# REPORTING
# ==========================================


def get_master_map(force_refresh=False):
    """Loads the map from disk if it exists, otherwise generates and saves it."""
    if CACHE_FILE.exists() and not force_refresh:
        print(f"Loading master map from cache: {CACHE_FILE}")
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    logging.info("Cache not found or refresh forced. Scanning English files...")
    master_map, _ = generate_id_map()  # We ignore master ID-less files for the cache

    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(master_map, f, indent=2, ensure_ascii=False)

    logging.info(f"Master map cached to {CACHE_FILE}")
    return master_map


def run_report(lang_ids, english_map):
    """
    Takes a pre-compiled set of language IDs and compares them
    against the English Master Map.
    """
    # Map English IDs to content name for grouping
    content_to_ids = defaultdict(set)
    for card_id, content in english_map.items():
        content_to_ids[content].add(card_id)

    # Analyze
    unsorted_report = {}

    for content, required_ids in content_to_ids.items():
        found = required_ids.intersection(lang_ids)
        missing = required_ids - lang_ids
        total, count = len(required_ids), len(found)
        percent = (count / total * 100) if total > 0 else 0

        unsorted_report[content] = {
            "completion": f"{percent:.2f} %",
            "stats": f"{count} / {total}",
            "missing": sorted(list(missing)),
        }

    # Sort alphabetically by content name
    sorted_report = {k: unsorted_report[k] for k in sorted(unsorted_report)}

    # Calculate orphans
    english_ids = set(english_map.keys())
    orphans = lang_ids - english_ids - NOT_ORPHANS

    # Exclude fan-made AND mini cards
    filtered_orphans = []
    for o in orphans:
        if len(o) > 15 and "-" in o:  # Check exclusion 1: Fan-made
            continue
        if o.endswith("-m"):  # Check exclusion 2: Mini-cards
            continue
        filtered_orphans.append(o)

    return sorted_report, sorted(list(filtered_orphans))


def save_report(
    content_data, lang_name, orphans, no_id_files, total_found, total_required
):
    # Build dictionary with specific key order for easier reading
    final_output = {
        "metadata": {
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "language": lang_name,
            "overall_completion": (
                f"{(total_found / total_required * 100):.2f} %"
                if total_required > 0
                else "0 %"
            ),
            "total_found": total_found,
            "total_required": total_required,
            "orphan_count": len(orphans),
            "missing_id_count": len(no_id_files),
        },
        "orphans": sorted(orphans),
        "files_without_id": sorted(no_id_files),
        "content": content_data,
    }

    filename = REPORT_PATH / f"{lang_name}_report.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2, ensure_ascii=False)


def find_language_folders():
    """
    Scans the LP_PATH and groups sibling folders by language name.
    Example output: { "German": [".../German - Campaigns", ".../German - Fan Campaigns"] }
    """
    languages = defaultdict(list)

    try:
        # Get all folders directly inside LP_PATH
        dirs = [
            d.name
            for d in LP_PATH.iterdir()
            if d.is_dir()
            and d.name not in EXCLUDED_FOLDERS
            and "Fan Campaigns" not in d.name
        ]

        for folder_name in dirs:
            # Split "German - Campaigns" -> "German"
            split = folder_name.split("-")
            lang_key = split[0].strip()
            languages[lang_key].append(LP_PATH / folder_name)
    except FileNotFoundError:
        logging.error(f"Language pack path not found: {LP_PATH}")
        return {}

    return dict(languages)


# ==========================================
# MAIN LOOP
# ==========================================

if __name__ == "__main__":
    # Ensure a reports directory exists
    REPORT_PATH.mkdir(parents=True, exist_ok=True)

    # Get the English Source of Truth
    english_id_map = get_master_map(True)  # Force refresh

    # Find and Group Folders
    all_languages = find_language_folders()

    print("\n" + "=" * 67)
    print(
        f"{'Language':<20} {'Progress':>10} {'Stats':>13} {'Orphans':>10} {'No-ID':>10}"
    )
    print("-" * 67)

    for lang_name, paths in sorted(all_languages.items()):
        # Aggregate IDs from all folders associated with this language
        aggregated_lang_ids = set()
        aggregated_no_ids = []

        for folder_path in paths:
            found_ids, no_ids = generate_lang_id_set(folder_path)
            aggregated_lang_ids.update(found_ids)
            aggregated_no_ids.extend(no_ids)

        # Run Analysis
        content_report, orphans = run_report(aggregated_lang_ids, english_id_map)

        # Stats calculation
        total_found = 0
        total_required = 0
        for data in content_report.values():
            found, required = map(int, data["stats"].split("/"))
            total_found += found
            total_required += required

        overall_pct = (total_found / total_required * 100) if total_required > 0 else 0

        # Aligned Console Output
        # Language: 20, Progress: 10 (8 for num + 2 for ' %'), Stats: 13, Orphans: 10, No-ID: 10
        pct_str = f"{overall_pct:>7.2f} %"
        stats_str = f"{total_found} / {total_required}"
        print(
            f"{lang_name:<20} "  # Column 1
            f"{pct_str:>10} "  # Column 2
            f"{stats_str:>13} "  # Column 3
            f"{len(orphans):>10} "  # Column 4
            f"{len(aggregated_no_ids):>10}"  # Column 5
        )

        # Export
        save_report(
            content_report,
            lang_name,
            orphans,
            aggregated_no_ids,
            total_found,
            total_required,
        )

    print("-" * 67)
    print(f"\nFull reports saved to: {REPORT_PATH}")
