#!/bin/bash
set -e

version=$(
    git describe --tags --match='v*' |
    sed -e 's/v//' -e 's/-/+/' -e 's/-/./'
)

sed -i -e "s/^__version__\s*=\s.*/__version__ = '$version'/" \
  infinitecopy/__init__.py

sed -i -e "s/^version\s*=\s.*/version = \"$version\"/" \
  pyproject.toml
