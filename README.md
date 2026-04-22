# Fluffy's Extensions

VS Code extensions for [pwn.college](https://pwn.college), packaged as a Docker image.

## Usage

```dockerfile
COPY --chown=0:0 --from=0xfluffyfluff/fluffys-extensions /run/challenge/share/code/extensions /run/challenge/share/code/extensions
```

> **Warning:** On pwn.college, `hacker` (uid 1000) is the default unprivileged shell. Files owned by `hacker` are world-writable, so the extensions must be owned by root to stay read-only.

## Extensions

| id | version | platform | source |
|----|---------|----------|--------|
| `catppuccin.catppuccin-vsc` | 3.18.1 | universal | Open VSX |
| `catppuccin.catppuccin-vsc-icons` | 1.26.0 | universal | Open VSX |
| `ms-vscode.cpptools` | 1.20.5 | linux-x64 | VS Marketplace |
| `ms-python.python` | 2024.14.1 | universal | Open VSX |
| `oderwat.indent-rainbow` | 8.3.1 | universal | Open VSX |

## Lock File Format

[`extensions.lock.json`](extensions.lock.json) has an `install_root` path and an `extensions` array. Each entry:

| field | type | description |
|-------|------|-------------|
| `id` | string | publisher.name extension ID |
| `version` | string | pinned version |
| `target_platform` | string | `universal` or a specific platform (e.g. `linux-x64`) |
| `folder` | string | destination directory name under `install_root` |
| `source` | string | `open-vsx` or `visualstudio-marketplace` |
| `url` | string | direct download URL for the `.vsix` |
| `sha256` | string | expected SHA-256 hex digest of the downloaded `.vsix` |
| `executable_paths` | string[] | *(optional)* paths inside the extension to mark `0o555` |

`executable_paths` is needed for extensions that ship native binaries (e.g. `ms-vscode.cpptools`). The installer checks that every declared path exists after extraction and fails if one is missing.

## Adding or Updating an Extension

1. Find the extension on [Open VSX](https://open-vsx.org) or the [VS Marketplace](https://marketplace.visualstudio.com).
2. Grab the direct download URL for the target version and platform.
3. Download the `.vsix` and compute its SHA-256:
   ```sh
   sha256sum extension.vsix
   ```
4. Add or update the entry in `extensions.lock.json`.
5. If the extension has native binaries, add the relative paths to `executable_paths`.
6. Rebuild the image to confirm the hash and extraction work.
