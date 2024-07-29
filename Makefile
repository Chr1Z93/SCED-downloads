SCED_TAG := main
TTS_MOD_MANAGER_VERSION := latest

ifeq ($(TTS_MOD_MANAGER_VERSION), latest)
TTS_MOD_MANAGER_URL := https://github.com/argonui/TTSModManager/releases/latest/download/TTSModManager-Linux
else
TTS_MOD_MANAGER_URL := https://github.com/argonui/TTSModManager/releases/download/$(TTS_MOD_MANAGER_VERSION)/TTSModManager-Linux
endif

init:
	curl -fOL $(TTS_MOD_MANAGER_URL) && chmod +x TTSModManager-Linux
	git clone https://github.com/argonui/SCED --branch $(SCED_TAG) SCED
build:
	python build.py
