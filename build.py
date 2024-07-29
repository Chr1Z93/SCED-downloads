import json
import subprocess
from pathlib import Path

INPUT_PATH = "decomposed"
OUTPUT_PATH = ".build"
MODDIR = "SCED"
MOD_EXECUTABLE = "./TTSModManager-Linux"


def read_library():
    with open("library.json") as f:
        data = json.load(f)
    return data["content"]


def exec_mod_manager(input_path, output_path):
    subprocess.run(
        [
            Path.cwd().joinpath(MOD_EXECUTABLE),
            "--objin",
            input_path,
            "--objout",
            output_path,
            "--moddir",
            MODDIR,
        ],
        check=True,
    )


def __main__():
    library = read_library()

    decomposed = [item for item in library if item["decomposed"]]

    for item in decomposed:
        input_path = next(
            Path.cwd().joinpath(INPUT_PATH, item["type"], item["name"]).glob("*.json")
        )

        output_path = Path.cwd().joinpath(OUTPUT_PATH, f'{item["filename"]}.json')
        output_path.parent.mkdir(parents=True, exist_ok=True)

        exec_mod_manager(input_path, output_path)


if __name__ == "__main__":
    __main__()
