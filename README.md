# SCED-downloads
A repository dedicated to hosting downloadable content for the **SCED** Tabletop Simulator mod.

## 🛠️ Mandatory Git Setting: Long Filenames
Due to deep folder nesting in this repository, **long file path support must be enabled** for Git on Windows to avoid errors:

```bash
git config --global core.longpaths true

```

## 📂 Repository Structure

The repository is organized into two main categories: individual decomposed files (for easier version control) and pre-bundled JSON objects.

```graphql
SCED-downloads/
│
├── decomposed/                  # Individual files (bundled automatically by the TTS Mod Manager)
│   └── [type]/                  # Folder matching the "type" field in library.json
│       └── [name]/              # Folder matching the "name" field in library.json
│
├── downloadable/                # Pre-bundled complete object data in .json format
│   └── [type]/                  # Folder matching the "type" field in library.json
│
├── library.json                 # Metadata manifest describing available content
└── README.md                    # This documentation
```

## 📄 library.json

The `library.json` file is a manifest that describes all downloadable content entries. Each entry in the `"content"` array defines a campaign, scenario, or player card expansion using the following schema:

| Key | Example Value | Description / Comment |
| --- | --- | --- |
| `name` | `"The Dunwich Legacy"` | The display name shown in the mod UI |
| `type` | `"campaign"` | Content category (e.g., `campaign`, `scenario`, `playercards`) |
| `author` | `"Fantasy Flight Games"` | The original creator or publisher |
| `scenariocount` | `11` | Number of contained scenarios (for campaigns) |
| `decomposed` | `true` | Set to `true` if content is stored as individual files |
| `cycle_code` | `"...-..."` | Sync code for [arkham.build](https://arkham.build) automatic loading |
| `filename` | `"the_dunwich_legacy"` | Folder name used to locate the asset on disk |
| `boxsize` | `"big"` | Display size category (e.g. big/small) |
| `boxart` | `"https://...jpg"` | Direct link to the box art image |
| `description` | `"A descent into..."` | Flavor text or summary of the content |

## 🌍 Language Packs

Language Packs provide localized card boxes with minimal metadata. They are designed to replace English counterparts within the mod based on unique IDs.

**Location:**
`decomposed/language-pack/` (e.g., `German - Campaigns/`, `Spanish - Player Cards/`)

### Workflow: Creating or Updating Packs

To maintain these packs, use the integrated VS Code tasks:

1. **Build:** Run the **"Build Saved Object"** task (selecting the main file) to generate the box.
2. **Edit:** Load the resulting object into Tabletop Simulator, add/modify cards, and save the object.
3. **Decompose:** Run the **"Decompose Saved Object"** task to break the saved object back down into the folder structure.


### 🔧 Cleanup Scripts

For data cleanup, refer to the [SCED-tools](https://github.com/Chr1Z93/SCED-tools/) repository, which contains scripts for:

* **Metadata Removal:** `language-pack-metadata-removal.py`
* **TTS Data Removal:** `default-data-removal.py`
* **Metadata Embedding:** `metadata-embedding.py`
* **Location Flipping:** `flip-location-sides.py` (if required)