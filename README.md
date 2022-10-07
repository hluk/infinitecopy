InfiniteCopy is simple cross-platform clipboard manager.

# Install and Run

There is no need to install the app. Single file executables are provided.

You can grab latest build artifacts from [a successful GitHub action
run](https://github.com/hluk/infinitecopy/actions?query=is%3Asuccess).

# Run from Source Code

## Requirements

The application requires to run recent enough versions of the following applications.

- Python
- PyQt5
- Qt Quick 5 libraries

## Run

To run the app execute following command.

```bash
python3 infinitecopy.py
```

# Development

**Qt 5** libraries must be installed on the system.

Clone repository and **start** the app with:

    poetry run python -m ensurepip --upgrade
    poetry install
    poetry run infinitecopy

Install **pre-commit** for local repository clone:

    pre-commit install

Run **all checks**:

    pre-commit run --all-files
    poetry run pytest
