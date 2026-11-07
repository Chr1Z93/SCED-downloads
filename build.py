import json
import subprocess
import sys
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
    result = subprocess.run(
        [
            resolve(PATHS["modexec"]),
            "--objin",
            input_path,
            "--objout",
            output_path,
            "--moddir",
            resolve(PATHS["moddir"]),
        ],
        capture_output=True,
        text=True,
    )

    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")

    if result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, result.args)
    if result.stdout.strip() or result.stderr.strip():
        raise RuntimeError("TTS Mod Manager produced output; treating this as a build failure.")


def sanitize_name(name):
    # Here we remove all occurrences of '(',')' and ',' / '''
    return name.replace("(", "").replace(")", "").replace(",", "").replace("'", "").strip()


def __main__():
    output_dir = resolve(PATHS["output"])
    output_dir.mkdir(parents=True, exist_ok=True)

    for item in [item for item in read_library() if item["decomposed"]]:
        sanitized_name = sanitize_name(item["name"])

        input_path = next(
            Path.cwd()
            .joinpath(PATHS["decomposed"], item["type"], sanitized_name)
            .glob("*.json"),
            None,
        )

        # Prevent NoneType error
        if input_path is None:
            print(f"Warning: No .json file found for item: {item['name']}")
            continue

        exec_mod_manager(
            input_path,
            output_dir.joinpath(f'{item["filename"]}.json'),
        )


if __name__ == "__main__":
    __main__()
