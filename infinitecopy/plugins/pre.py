import logging

from infinitecopy import Plugin, formats

SECRET_FORMATS = [
    "x-kde-passwordManagerHint",
    'application/x-qt-windows-mime;value="Clipboard Viewer Ignore"',
]

logger = logging.getLogger(__name__)


class AvoidSpuriousChangesPlugin(Plugin):
    """
    Avoids processing spurious clipboard/selection change events.
    """

    def __init__(self, app):
        super().__init__(app)
        self.lastData = {}

    def onClipboardChanged(self, data):
        source = data.get(formats.mimeSource)
        if self.lastData.get(source) == data:
            return False

        self.lastData[source] = data
        return True


class IgnoreSecretsPlugin(Plugin):
    """Stops processing secrets and passwords."""

    def __init__(self, app):
        super().__init__(app)
        app.clipboard.formats.extend(SECRET_FORMATS)

    def onClipboardChanged(self, data):
        if any(format in data for format in SECRET_FORMATS):
            logger.info("Ignoring copied secret")
            return False
        return True
