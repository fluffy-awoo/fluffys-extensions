# Agent Context

This repo packages VS Code extensions for pwn.college as a Docker image. The only files that matter for the build are `extensions.lock.json`, `scripts/install_extensions.py`, and `Dockerfile`.

## How extensions are installed

`scripts/install_extensions.py` reads `extensions.lock.json`, downloads each `.vsix`, verifies its SHA-256, extracts the inner `extension/` directory into `/run/challenge/share/code/extensions/<folder>`, and writes a `extensions.json` index that VS Code reads to discover pre-installed extensions.

All files are set `0o444` (read-only) after extraction. Files listed in `executable_paths` get `0o555` instead. This is intentional — on pwn.college, `hacker` (uid 1000) is the default unprivileged user and files owned by uid 1000 would be world-writable.

## Adding or updating an extension

Edit `extensions.lock.json`. Each entry needs:

- `id`: `publisher.extensionName` (e.g. `ms-python.python`)
- `version`: exact version string
- `target_platform`: `universal` for pure-JS extensions, `linux-x64` for extensions with native binaries
- `folder`: conventionally `<id>-<version>` or `<id>-<version>-<platform>` for platform-specific ones
- `source`: `open-vsx` or `visualstudio-marketplace`
- `url`: direct `.vsix` download URL
- `sha256`: SHA-256 hex digest of the `.vsix`
- `executable_paths`: list of paths inside the extracted extension that need to be executable (only needed for extensions with native binaries like `ms-vscode.cpptools`)

### Finding the URL

**Open VSX:** `https://open-vsx.org/api/<Publisher>/<name>/<version>/file/<Publisher>.<name>-<version>.vsix`

Example: `https://open-vsx.org/api/oderwat/indent-rainbow/8.3.1/file/oderwat.indent-rainbow-8.3.1.vsix`

**VS Marketplace:** `https://marketplace.visualstudio.com/_apis/public/gallery/publishers/<publisher>/vsextensions/<name>/<version>/vspackage?targetPlatform=<platform>`

Example: `https://marketplace.visualstudio.com/_apis/public/gallery/publishers/ms-vscode/vsextensions/cpptools/1.20.5/vspackage?targetPlatform=linux-x64`

### Computing the SHA-256

```sh
curl -L <url> -o extension.vsix
sha256sum extension.vsix
```

### executable_paths

For extensions like `ms-vscode.cpptools` that ship native binaries, you need to declare the paths that should be executable. Extract the `.vsix` (it's a ZIP) and inspect which binaries are inside:

```sh
unzip -l extension.vsix | grep -v '/$' | awk '{print $4}' | grep 'bin/'
```

Paths are relative to the extracted `extension/` directory (i.e. without the `extension/` prefix).

## Docker image

Published to Docker Hub as `0xfluffyfluff/fluffys-extensions:latest`. Built on push to `master` if `*.py`, `*.json`, or `Dockerfile` changed. The image is a two-stage build — the builder stage does all the downloading, the runtime stage just copies the result.

The image is used in pwn.college Dockerfiles like:

```dockerfile
COPY --chown=0:0 --from=0xfluffyfluff/fluffys-extensions /run/challenge/share/code/extensions /run/challenge/share/code/extensions
```

`--chown=0:0` is required. See the README warning for why.
