#!/bin/bash
set -e

version=$(
    git describe --match='v*' |
    sed -e 's/v//' -e 's/-/+/' -e 's/-/./'
)

sed -i -e "s/^__version__\s*=\s.*/__version__ = '$version'/" \
  infinitecopy/__init__.py

poetry version "$version"
