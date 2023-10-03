# SPDX-License-Identifier: LGPL-2.0-or-later
import logging

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


def command_count(app, client):
    count = app.clipboardItemModel.getItemCount()
    client.sendPrint(str(count).encode("utf-8"))


def command_add(app, client):
    app.clipboardItemModel.beginTransaction()
    for text in client.receiveCommandArguments():
        logger.debug("command_add: Adding text item: %d bytes", len(text))
        app.clipboardItemModel.addItemNoCommit({formats.mimeText: text})
    app.clipboardItemModel.endTransaction()
    app.clipboardItemModel.select()


def command_get(app, client):
    sep = "\n"
    write_sep = False
    for arg in client.receiveCommandArguments():
        try:
            row = int(arg)
        except ValueError:
            sep = unescape(arg)
            continue

        if write_sep and sep:
            client.sendPrint(sep)
        write_sep = True

        text = app.clipboardItemModel.getItem(row)
        if text:
            client.sendPrint(text)


def command_paste(app, client):
    if app.paster is None:
        logger.warning("Pasting text is unsupported")
    else:
        logger.info("Pasting text")
        for data in client.receiveCommandArguments():
            text = bytes(data).decode("utf-8")
            if not app.paster.paste(text):
                logger.warning("Failed to paste text")
                break
