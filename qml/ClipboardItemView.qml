// SPDX-License-Identifier: LGPL-2.0-or-later
import QtQuick

TableView {
    id: listView
    focus: true
    keyNavigationEnabled: true
    pointerNavigationEnabled: false
    alternatingRows: true
    delegate: ClipboardItem {
        view: listView
    }
    selectionModel: ItemSelectionModel {}

    // Fix item sizes
    reuseItems: false

    function currentData() {
        var selected = clipboardItemView.selectionModel.selectedIndexes
        if (selected.length > 0) {
            var text = ""
            for (const index of selected) {
                const item = itemAtIndex(index)
                if (text)
                    text += "\n"
                text += item.text
            }
            return {"text/plain": text}
        } else if (clipboardItemView.currentRow >= 0) {
            const index = listView.index(clipboardItemView.currentRow, 0)
            const item = itemAtIndex(index)
            return item.dataDict
        }
        return {}
    }
}
