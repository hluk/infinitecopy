# SPDX-License-Identifier: LGPL-2.0-or-later
import logging

from PySide6.QtCore import QByteArray

import infinitecopy.MimeFormats as formats

logger = logging.getLogger(__name__)


def command_show(app, stream, socket):
    logger.debug("Activating window")
    app.view.hide()
    app.view.show()


def command_add(app, stream, socket):
    app.clipboardItemModel.beginTransaction()
    while not socket.atEnd():
        text = stream.readQVariant()
        app.clipboardItemModel.addItemNoCommit(
            {formats.mimeText: QByteArray(text.encode("utf-8"))}
        )
    app.clipboardItemModel.endTransaction()
    app.clipboardItemModel.submitChanges()


def command_get(app, stream, socket):
    while not socket.atEnd():
        row = int(stream.readQVariant())
        index = app.filterProxyModel.index(row, 0)
        role = app.clipboardItemModel.itemTextRole
        data = app.filterProxyModel.data(index, role)
        stream.writeQVariant(data)


def command_paste(app, stream, socket):
    if app.paster is None:
        logger.warning("Pasting text is unsupported")
    else:
        logger.info("Pasting text")
        while not socket.atEnd():
            text = stream.readQVariant()
            if not app.paster.paste(text):
                logger.warning("Failed to paste text")
                break
