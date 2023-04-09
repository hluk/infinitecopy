# SPDX-License-Identifier: LGPL-2.0-or-later
import logging
import os

import infinitecopy.MimeFormats as formats
from infinitecopy.Clipboard import Clipboard
from infinitecopy.WaylandClipboard import WaylandClipboard

logger = logging.getLogger(__name__)


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
        if os.environ.get("INFINITECOPY_GENERIC_CLIPBOARD") != "1":
            clipboard = WaylandClipboard(config)
            if clipboard.isOk():
                return clipboard

        logger.warning("Using generic non-wayland clipboard access")

    return Clipboard(config)
