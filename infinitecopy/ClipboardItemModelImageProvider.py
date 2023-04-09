# SPDX-License-Identifier: LGPL-2.0-or-later
from PySide6.QtGui import QPixmap
from PySide6.QtQuick import QQuickImageProvider


class ClipboardItemModelImageProvider(QQuickImageProvider):
    def __init__(self, model):
        QQuickImageProvider.__init__(self, QQuickImageProvider.Pixmap)
        self.model = model

    def requestPixmap(self, id, size, _requestedSize):
        row = int(id)

        if row < 0 or row >= self.model.rowCount():
            return QPixmap()

        data = self.model.imageData(row)
        if data is None:
            return QPixmap()

        pixmap = QPixmap()
        if not pixmap.loadFromData(data):
            return QPixmap()

        return pixmap
