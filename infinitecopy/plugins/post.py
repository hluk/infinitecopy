from infinitecopy import Plugin, formats

AVOID_DUPLICATES_SOURCES = (
    formats.valueSourceClipboard,
    formats.valueSourceSelection,
)


def setup(app):
    avoid_duplicates(app)


def avoid_duplicates(app):
    """Avoid keeping duplicate clipboard/selection items."""

    model = app.clipboardItemModel

    def on_model_reset():
        record = model.record(0)

        source = record.value("source")
        if source not in AVOID_DUPLICATES_SOURCES:
            return

        hash_ = record.value("hash")
        if not hash_:
            return

        keep_id = record.value("id")
        model.executeQuery(
            "DELETE FROM item WHERE hash = :hash AND id != :keep_id",
            hash=hash_,
            keep_id=keep_id,
        )

    model.modelReset.connect(on_model_reset)


class AddItemPlugin(Plugin):
    def onClipboardChanged(self, data):
        self.app.clipboardItemModel.addItemNoEmpty(data)
