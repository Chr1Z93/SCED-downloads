from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import logging
import json
import os
import pathlib
import time

# Config
ROOT_PATH = pathlib.Path(r"C:\git\SCED-downloads\decomposed")
REPORT_PATH = pathlib.Path(r"C:\git\SCED-downloads\misc\localization_reports")
EXCLUDED_FOLDERS = {"language-pack", "misc", ".git", ".vscode"}
NOT_ORPHANS = {
    "LatestFAQ",
    "LearnToPlay",
    "PhaseReference",
    "RoundSequence",
    "RulesReference",
}

# Derived Data
LP_PATH = ROOT_PATH / "language-pack"
SCRIPT_DIR = pathlib.Path(__file__).parent.absolute()
CACHE_FILE = SCRIPT_DIR / "language-pack-completion-stats_cache.json"


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


# Skip fanmade content for now
def get_id(gm_data):
    if "TtsZoopGuid" in gm_data:
        return None
    return gm_data.get("id")


def process_file(dirpath, filename):
    file_path = os.path.join(dirpath, filename)
    found_id = None

    try:
        # Extract the ID (external .gmnotes)
        gmnotes_file = os.path.splitext(file_path)[0] + ".gmnotes"
        if os.path.exists(gmnotes_file):
            with open(gmnotes_file, "r", encoding="utf-8") as f:
                gm_data = json.load(f)
                found_id = get_id(gm_data)

        if not found_id:
            # Extract the ID (internal)
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                gm_notes_raw = data.get("GMNotes", "")
                if gm_notes_raw:
                    try:
                        gm_data = json.loads(gm_notes_raw)
                        found_id = get_id(gm_data)
                    except (json.JSONDecodeError, TypeError):
                        pass

        if not found_id:
            return None

        # Split the full path into a list of folder names
        path_parts = dirpath.split(os.sep)

        try:
            # Find where "decomposed" sits in the path and grab the two levels after
            # Example: .../decomposed/campaign/Night of the Zealot/cards -> "campaign/Night of the Zealot"
            idx = path_parts.index("decomposed")
            main_folder = os.path.join(path_parts[idx + 1], path_parts[idx + 2])
            return str(found_id), main_folder
        except (ValueError, IndexError):
            return None

    except Exception:
        return None


def generate_id_map():
    id_to_folder_map = {}
    tasks = []

    start_time = time.perf_counter()

    # Scanning Phase
    logging.info(f"Starting scan in {ROOT_PATH}")
    with ThreadPoolExecutor(max_workers=8) as executor:
        for dirpath, dirs, filenames in os.walk(ROOT_PATH):
            # This modifies the dirs list in-place, so os.walk won't visit them
            dirs[:] = [d for d in dirs if d not in EXCLUDED_FOLDERS]

            for filename in filenames:
                if filename.endswith(".json"):
                    tasks.append(executor.submit(process_file, dirpath, filename))

        scan_done = time.perf_counter()
        logging.info(
            f"Scan complete. Found {len(tasks)} JSON files in {scan_done - start_time:.2f}s"
        )

        # Processing Phase
        for task in tasks:
            result = task.result()
            if result:
                card_id, folder_path = result
                id_to_folder_map[card_id] = folder_path

    end_time = time.perf_counter()
    logging.info(f"Processing complete in {end_time - scan_done:.2f}s")
    logging.info(f"Total time: {end_time - start_time:.2f}s")

    return id_to_folder_map


def generate_lang_id_set(lang_root):
    """
    Crawls the language folder and returns a simple set of all found IDs.
    We reuse the 'process_file' logic but ignore the 'main_folder' return.
    """
    found_ids = set()
    tasks = []

    with ThreadPoolExecutor(max_workers=8) as executor:
        for dirpath, dirs, filenames in os.walk(lang_root):
            # Still exclude noise
            dirs[:] = [d for d in dirs if d not in EXCLUDED_FOLDERS]
            for filename in filenames:
                if filename.endswith(".json"):
                    tasks.append(executor.submit(process_file, dirpath, filename))

        for task in tasks:
            result = task.result()
            if result:
                card_id, _ = result  # We ignore the folder here
                found_ids.add(card_id)

    return found_ids


def get_master_map(force_refresh=False):
    """Loads the map from disk if it exists, otherwise generates and saves it."""
    if os.path.exists(CACHE_FILE) and not force_refresh:
        print(f"Loading master map from cache: {CACHE_FILE}")
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    logging.info("Cache not found or refresh forced. Scanning English files...")
    master_map = generate_id_map()

    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(master_map, f, indent=2)

    logging.info(f"Master map cached to {CACHE_FILE}")
    return master_map


def run_report(lang_ids, english_map):
    """
    Takes a pre-compiled set of language IDs and compares them
    against the English Master Map.
    """
    # Map English IDs to their Campaigns for grouping
    campaign_to_ids = defaultdict(set)
    for card_id, campaign in english_map.items():
        campaign_to_ids[campaign].add(card_id)

    # Analyze
    unsorted_report = {}
    english_ids = set(english_map.keys())
    orphans = lang_ids - english_ids - NOT_ORPHANS

    for campaign, required_ids in campaign_to_ids.items():
        found = required_ids.intersection(lang_ids)
        missing = required_ids - lang_ids

        total = len(required_ids)
        count = len(found)
        percent = (count / total * 100) if total > 0 else 0

        unsorted_report[campaign] = {
            "completion": f"{percent:.2f}%",
            "stats": f"{count}/{total}",
            "missing": sorted(list(missing)),
        }

    # Sort alphabetically by campaign name
    sorted_report = {k: unsorted_report[k] for k in sorted(unsorted_report)}

    return sorted_report, sorted(list(orphans))


def save_report(campaign_data, lang_name, total_found, total_required):
    final_output = {
        "metadata": {
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "language": lang_name,
            "stats": {
                "overall_completion": (
                    f"{(total_found / total_required * 100):.2f}%"
                    if total_required > 0
                    else "0%"
                ),
                "total_found": total_found,
                "total_required": total_required,
                "orphan_count": len(orphans),
            },
        },
        "orphans": orphans,
        "campaigns": campaign_data,
    }

    filename = os.path.join(REPORT_PATH, f"{lang_name}_report.json")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2)


def find_language_folders():
    """
    Scans the LP_PATH and groups sibling folders by language name.
    Example output: { "German": [".../German - Campaigns", ".../German - Fan Campaigns"] }
    """
    languages = defaultdict(list)

    try:
        # Get all folders directly inside LP_PATH
        dirs = [
            d
            for d in os.listdir(LP_PATH)
            if os.path.isdir(os.path.join(LP_PATH, d)) and d not in EXCLUDED_FOLDERS
        ]

        for folder_name in dirs:
            # Split "German - Campaigns" -> "German"
            split = folder_name.split("-")
            type_key = split[1].strip()

            # Skip player cards
            if type_key == "Player Cards":
                continue

            lang_key = split[0].strip()
            full_path = os.path.join(LP_PATH, folder_name)
            languages[lang_key].append(full_path)

    except FileNotFoundError:
        logging.error(f"Language pack path not found: {LP_PATH}")
        return {}

    return dict(languages)


if __name__ == "__main__":
    # Ensure a reports directory exists
    if not os.path.exists(REPORT_PATH):
        os.makedirs(REPORT_PATH)

    # Get the English Source of Truth
    english_id_map = get_master_map()

    # Find and Group Folders
    all_languages = find_language_folders()

    print("Reports for language pack completion have been created. Summary:\n")
    for lang_name, paths in all_languages.items():
        # Aggregate IDs from all folders associated with this language
        aggregated_lang_ids = set()
        for folder_path in paths:
            found_in_sub = generate_lang_id_set(folder_path)
            aggregated_lang_ids.update(found_in_sub)

        # Run Analysis
        campaign_report, orphans = run_report(aggregated_lang_ids, english_id_map)

        # Console Summary
        total_found = 0
        total_required = 0
        for data in campaign_report.values():
            found, required = map(int, data["stats"].split("/"))
            total_found += found
            total_required += required

        overall_pct = (total_found / total_required * 100) if total_required > 0 else 0

        # Aligned Console Output
        # lang_name: left-aligned (20 chars), pct: right-aligned (6 chars)
        # found/total: right-aligned (11 chars)
        print(
            f"{lang_name:<20} {overall_pct:>6.2f} %  ({total_found:>4}/{total_required:<4}) {len(orphans):>3} orphans"
        )

        # Export
        campaign_report["orphans"] = orphans
        save_report(campaign_report, lang_name, total_found, total_required)

    print(f"\nFull reports saved to: {REPORT_PATH}")
