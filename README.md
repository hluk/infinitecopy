InfiniteCopy is simple cross-platform clipboard manager.

# Install and Run

There is no need to install the app. Single file executables are provided.

You can grab latest build artifacts from [a successful GitHub action
run](https://github.com/hluk/infinitecopy/actions?query=is%3Asuccess).

# Run from Source Code

Clone repository and **start** the app with:

    poetry run python -m ensurepip --upgrade
    poetry install
    poetry run infinitecopy

Install **pre-commit** for local repository clone:

    pre-commit install

Run **all checks**:

    pre-commit run --all-files
    poetry run pytest

# Plugins

Plugins are dynamically loaded Python modules in user configuration directory
that allow making to act on new clipboard content.

You can add custom plugins to configuration directory. Usually the path is:

- on Linux: `~/.config/InfiniteCopy/plugins`
- on Windows: `C:/Users/<USER>/AppData/Local/InfiniteCopy/plugins`
- on macOs: `~/Library/Preferences/InfiniteCopy/plugins`

See predefined plugins:

- [infinitecopy/plugins/pre.py](infinitecopy/plugins/pre.py)
- [infinitecopy/plugins/post.py](infinitecopy/plugins/post.py)
