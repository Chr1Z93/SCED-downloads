import json
import subprocess
from pathlib import Path

PATHS = {
    "decomposed": "./decomposed",
    "library": "./library.json",
    "moddir": "./SCED",
    "modexec": "./TTSModManager-Linux",
    "output": "./.build",
}


def resolve(path):
    return Path.cwd().joinpath(path)


def read_library():
    with open(resolve(PATHS["library"])) as f:
        data = json.load(f)
    return data["content"]


def exec_mod_manager(input_path, output_path):
    subprocess.run(
        [
            resolve(PATHS["modexec"]),
            "--objin",
            input_path,
            "--objout",
            output_path,
            "--moddir",
            resolve(PATHS["moddir"]),
        ],
        check=True,
    )


def __main__():
    output_dir = resolve(PATHS["output"])
    output_dir.mkdir(parents=True, exist_ok=True)

    for item in [item for item in read_library() if item["decomposed"]]:
        exec_mod_manager(
            next(
                Path.cwd()
                .joinpath(PATHS["decomposed"], item["type"], item["name"])
                .glob("*.json")
            ),
            output_dir.joinpath(f'{item["filename"]}.json'),
        )


if __name__ == "__main__":
    __main__()
