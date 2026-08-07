import csv
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import requests

# ============================================================
# Configuration
# ============================================================

OWNER = "Chr1Z93"
REPO = "SCED-downloads"

# Only include releases from this date onwards
CUTOFF_DATE = datetime(2024, 1, 1, tzinfo=timezone.utc)

TOKEN = None
PER_PAGE = 100

# ============================================================

session = requests.Session()
session.headers.update({"Accept": "application/vnd.github+json"})

if TOKEN:
    session.headers.update({"Authorization": f"Bearer {TOKEN}"})


def get_all_releases():
    """Download releases newer than CUTOFF_DATE."""

    releases = []
    page = 1

    while True:
        response = session.get(
            f"https://api.github.com/repos/{OWNER}/{REPO}/releases",
            params={"per_page": PER_PAGE, "page": page},
        )

        response.raise_for_status()
        batch = response.json()

        if not batch:
            break

        stop = False

        for release in batch:
            published = datetime.fromisoformat(
                release["published_at"].replace("Z", "+00:00")
            )

            if published < CUTOFF_DATE:
                stop = True
                break

            releases.append(release)

        print(f"Loaded page {page} ({len(releases)} matching releases)")

        if stop:
            break

        page += 1

    return releases


def export_releases_as_csv():
    releases = get_all_releases()
    print(f"\nTotal releases: {len(releases)}")

    script_dir = Path(__file__).resolve().parent
    output_dir = script_dir / "download_stats"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_releases = output_dir / "release_downloads.csv"
    output_assets = output_dir / "asset_downloads.csv"
    asset_totals = defaultdict(int)

    with output_releases.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.writer(file)
        writer.writerow(["release", "published", "asset", "downloads"])

        for release in releases:
            tag = release["tag_name"]
            published = release["published_at"]

            for asset in release["assets"]:
                name = asset["name"]
                downloads = asset["download_count"]
                writer.writerow([tag, published, name, downloads])
                asset_totals[name] += downloads

    with output_assets.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.writer(file)
        writer.writerow(["asset", "total_downloads"])

        for asset, downloads in sorted(
            asset_totals.items(),
            key=lambda x: x[1],
            reverse=True,
        ):
            writer.writerow([asset, downloads])

    print(f"\nCreated:")
    print(f"  {output_releases}")
    print(f"  {output_assets}")


if __name__ == "__main__":
    export_releases_as_csv()
