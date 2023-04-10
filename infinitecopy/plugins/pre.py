import logging

from infinitecopy import Plugin

SECRET_FORMATS = [
    "x-kde-passwordManagerHint",
    'application/x-qt-windows-mime;value="Clipboard Viewer Ignore"',
]

logger = logging.getLogger(__name__)


class IgnoreSecretsPlugin(Plugin):
    def __init__(self, app):
        super().__init__(app)
        app.clipboard.formats.extend(SECRET_FORMATS)

    def onClipboardChanged(self, data):
        if any(format in data for format in SECRET_FORMATS):
            logger.info("Ignoring copied secret")
            return False
