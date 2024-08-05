# Define the tag for SCED repository
SCED_TAG := main

# Define the version for TTS Mod Manager
TTS_MOD_MANAGER_VERSION := v1.1.1

# Determine the URL for TTS Mod Manager based on version
ifeq ($(TTS_MOD_MANAGER_VERSION), latest)
TTS_MOD_MANAGER_URL := https://github.com/argonui/TTSModManager/releases/latest/download/TTSModManager-Linux
else
TTS_MOD_MANAGER_URL := https://github.com/argonui/TTSModManager/releases/download/$(TTS_MOD_MANAGER_VERSION)/TTSModManager-Linux
endif

# Initialize the project
# Copy contents of src/xml directory to the cloned SCED repository for Lua/XML bundling
init:
	curl -fOL $(TTS_MOD_MANAGER_URL) && chmod +x TTSModManager-Linux
	git clone https://github.com/argonui/SCED --branch $(SCED_TAG) SCED
	cp -R src/* SCED/src/
	cp -R xml/* SCED/xml/

# Build the project
build:
	python build.py