# SPDX-License-Identifier: LGPL-2.0-or-later
import logging

from PySide6.QtCore import Qt

import infinitecopy.MimeFormats as formats

logger = logging.getLogger(__name__)


def unescape(escaped):
    return bytes(escaped).decode("unicode_escape")


def is_active(app):
    return app.app.focusWindow() is not None


def command_show(app, _client):
    logger.debug("Activating window")
    app.view.hide()
    app.view.show()


def command_hide(app, _client):
    logger.debug("Deactivating window")
    app.view.hide()


def command_toggle(app, client):
    if is_active(app):
        command_hide(app, client)
    else:
        command_show(app, client)


def command_active(app, client):
    if not is_active(app):
        client.sendExit(1)


def command_quit(app, _client):
    app.app.quit()


def command_add(app, client):
    app.clipboardItemModel.beginTransaction()
    while not client.atEnd():
        text = client.receive()
        app.clipboardItemModel.addItemNoCommit({formats.mimeText: text})
    app.clipboardItemModel.endTransaction()
    app.clipboardItemModel.submitChanges()


def command_get(app, client):
    sep = "\n"
    write_sep = False
    column = app.clipboardItemModel.textColumn
    while not client.atEnd():
        arg = client.receive()
        try:
            row = int(arg)
        except ValueError:
            sep = unescape(arg)
            continue

        if write_sep and sep:
            client.sendPrint(sep)
        write_sep = True

        index = app.filterProxyModel.index(row, column)
        data = app.filterProxyModel.data(index, Qt.DisplayRole)
        if data:
            client.sendPrint(data)


def command_paste(app, client):
    if app.paster is None:
        logger.warning("Pasting text is unsupported")
    else:
        logger.info("Pasting text")
        while not client.atEnd():
            text = bytes(client.receive()).decode("utf-8")
            if not app.paster.paste(text):
                logger.warning("Failed to paste text")
                break
