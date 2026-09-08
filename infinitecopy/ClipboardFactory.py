# SPDX-License-Identifier: LGPL-2.0-or-later
import logging
import os
from dataclasses import dataclass, field

import infinitecopy.MimeFormats as formats
from infinitecopy.Clipboard import Clipboard
from infinitecopy.WaylandClipboard import WaylandClipboard

logger = logging.getLogger(__name__)


DEFAULT_FORMARTS = (
    formats.mimeText,
    formats.mimeHtml,
    formats.mimePng,
    formats.mimeSvg,
)


@dataclass
class ClipboardConfig:
    clipboardChangedDelayMs = 500
    selectionChangedDelayMs = 1000
    formats: list[str] = field(default_factory=lambda: list(DEFAULT_FORMARTS))


def createClipboard():
    config = ClipboardConfig()

    if os.environ.get("WAYLAND_DISPLAY"):
        if os.environ.get("INFINITECOPY_GENERIC_CLIPBOARD") != "1":
            clipboard = WaylandClipboard(config)
            if clipboard.isOk():
                return clipboard

        logger.warning("Using generic non-wayland clipboard access")

    return Clipboard(config)
