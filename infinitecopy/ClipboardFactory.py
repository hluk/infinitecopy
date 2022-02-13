# SPDX-License-Identifier: LGPL-2.0-or-later
import os

import infinitecopy.MimeFormats as formats
from infinitecopy.Clipboard import Clipboard
from infinitecopy.WaylandClipboard import WaylandClipboard


class ClipboardConfig:
    clipboardChangedDelayMs = 500
    selectionChangedDelayMs = 1000
    formats = [
        formats.mimeText,
        formats.mimeHtml,
        formats.mimePng,
        formats.mimeSvg,
    ]


def createClipboard():
    config = ClipboardConfig()

    if os.environ.get("WAYLAND_DISPLAY"):
        clipboard = WaylandClipboard(config)
    else:
        clipboard = Clipboard(config)

    return clipboard
