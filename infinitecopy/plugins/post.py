from infinitecopy import Plugin


class AddItemPlugin(Plugin):
    def onClipboardChanged(self, data):
        self.app.clipboardItemModel.addItemNoEmpty(data)
