# SCED-downloads
A repository to host downloadable content for SCED.

## Git setting: long filenames
Due to deep folder nesting in this repository, long file path support must be enabled for Git on Windows:
```
git config --global core.longpaths true
```

## Repository Structure

This repository is primarily structured around downloadable content packs, with metadata and assets organized for use in SCED.
```graphql
SCED-downloads/
│
├── campaign/                           # Folder matching the "type" field in library.json (campaign / scenario / playercards)
│   ├── decomposed/                     # Decomposed files (bundled automatically by the TTS Mod Manager)
│   │   ├── The Night of the Zealot/    # Folder matching the "name" field in library.json
│   │   └── The Dunwich Legacy/
│   └── downloadable/                   # Pre-bundled complete object data in JSON format
│
├── library.json                        # Metadata file describing available downloadable content
└── README.md                           # This documentation file
```
## `library.json`

The `library.json` file is a manifest that describes all downloadable content entries. Each entry in the `"content"` array represents a campaign, scenario or player card expansion with the following structure:
```
{
  "name": "The Dunwich Legacy",         // Display name
  "type": "campaign",                   // Content type (e.g. campaign, scenario, playercards)
  "author": "Fantasy Flight Games",     // Content creator
  "decomposed": true,                   // Whether the content is stored in decomposed (individual files) form
  "cycle_code": "...-...",              // Code to match this content with arkham.build and allow automatic loading
  "filename": "the_dunwich_legacy",     // Folder name used to locate this content
  "boxsize": "big",                     // Display size category (e.g. big/small)
  "boxart": "https://...jpg",           // Link to box art image
  "description": "..."                  // Flavor text or summary
}
```
