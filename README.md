InfiniteCopy is clipboard manager designed to run both desktop and mobile devices.

The application is in very early stage!

## Requirements

The application requires to run recent enough versions of the following applications.

- Python3
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

    poetry install
    poetry run xitomatl

Install **pre-commit** for local repository clone:

    pre-commit install

Run **all checks**:

    pre-commit run --all-files
    poetry run pytest
