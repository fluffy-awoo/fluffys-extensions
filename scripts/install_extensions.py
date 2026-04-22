#!/usr/bin/env python3
import argparse
import gzip
import hashlib
import json
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("lock_file", type=Path)
    parser.add_argument("destination", type=Path)
    return parser.parse_args()


def require_string(extension, key):
    value = extension.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{extension.get('id', '<unknown>')}: missing {key}")
    return value


def download(url, destination):
    request = urllib.request.Request(
        url,
        headers={
            "Accept-Encoding": "gzip",
            "User-Agent": "fluffy/1.0",
        },
    )

    for attempt in range(1, 6):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                stream = response
                if response.headers.get("Content-Encoding", "").lower() == "gzip":
                    stream = gzip.GzipFile(fileobj=response)

                with destination.open("wb") as output:
                    shutil.copyfileobj(stream, output)
            return
        except (OSError, urllib.error.URLError) as error:
            if attempt == 5:
                raise
            print(f"Download failed ({attempt}/5): {error}", file=sys.stderr)
            time.sleep(min(attempt * 2, 10))


def sha256sum(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def reset_destination(path):
    path.mkdir(parents=True, exist_ok=True)
    for child in path.iterdir():
        if child.is_dir() and not child.is_symlink():
            shutil.rmtree(child)
        else:
            child.unlink()


def set_readonly_tree(path):
    for child in path.rglob("*"):
        if child.is_dir():
            child.chmod(0o755)
        elif child.is_file():
            child.chmod(0o444)


def install_extension(extension, destination):
    extension_id = require_string(extension, "id")
    folder = require_string(extension, "folder")
    url = require_string(extension, "url")
    expected_sha256 = require_string(extension, "sha256")
    target = destination / folder

    with tempfile.TemporaryDirectory() as temp_root:
        temp_root = Path(temp_root)
        vsix_path = temp_root / "extension.vsix"
        extract_path = temp_root / "extract"

        print(f"Fetching {extension_id}")
        download(url, vsix_path)

        actual_sha256 = sha256sum(vsix_path)
        if actual_sha256 != expected_sha256:
            raise ValueError(
                f"{extension_id}: sha256 mismatch: expected {expected_sha256}, got {actual_sha256}"
            )

        with zipfile.ZipFile(vsix_path) as archive:
            archive.extractall(extract_path)

        extension_root = extract_path / "extension"
        if not extension_root.is_dir():
            raise ValueError(f"{extension_id}: VSIX does not contain extension/")

        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(extension_root, target)

        manifest = extract_path / "extension.vsixmanifest"
        if manifest.is_file():
            shutil.copy2(manifest, target / ".vsixmanifest")

    set_readonly_tree(target)
    for relative_path in extension.get("executable_paths", []):
        executable = target / relative_path
        if not executable.is_file():
            raise ValueError(
                f"{extension_id}: declared executable missing: {relative_path}"
            )
        executable.chmod(0o555)


def metadata_for(extension):
    source = require_string(extension, "source")
    metadata_source = "gallery" if source == "open-vsx" else "vsix"
    return {
        "source": metadata_source,
        "targetPlatform": require_string(extension, "target_platform"),
    }


def write_extensions_json(lock, destination):
    entries = []
    for extension in lock["extensions"]:
        folder = require_string(extension, "folder")
        entries.append(
            {
                "identifier": {"id": require_string(extension, "id")},
                "version": require_string(extension, "version"),
                "location": {
                    "$mid": 1,
                    "path": str(destination / folder),
                    "scheme": "file",
                },
                "relativeLocation": folder,
                "metadata": metadata_for(extension),
            }
        )

    output = destination / "extensions.json"
    output.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")
    output.chmod(0o444)


def main():
    args = parse_args()
    if not args.lock_file.is_file():
        raise FileNotFoundError(args.lock_file)
    if str(args.destination) == "/":
        raise ValueError("Refusing to write extensions to /")

    lock = json.loads(args.lock_file.read_text(encoding="utf-8"))
    extensions = lock.get("extensions")
    if not isinstance(extensions, list) or not extensions:
        raise ValueError("Lock file must contain a non-empty extensions list")

    reset_destination(args.destination)
    for extension in extensions:
        install_extension(extension, args.destination)
    write_extensions_json(lock, args.destination)

    print(f"Installed {len(extensions)} extensions into {args.destination}")


if __name__ == "__main__":
    main()
