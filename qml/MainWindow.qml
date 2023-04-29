// SPDX-License-Identifier: LGPL-2.0-or-later
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ColumnLayout {
    Accessible.name: "infinitecopy main window"

    anchors.fill: parent

    FilterTextField {
        id: filterTextField
        z: 2

        Accessible.description: "filter items text field"

        Layout.fillWidth: true
        model: clipboardItemView.model

        KeyNavigation.tab: clipboardItemView
        KeyNavigation.down: clipboardItemView
    }

    ClipboardItemView {
        id: clipboardItemView
        z: 1

        Accessible.name: "item list"

        Layout.fillHeight: true
        Layout.fillWidth: true

        model: clipboardItemModelFilterProxy

        // Keep a row selected after list updates.
        property int lastCurrentRow: 0
        property string lastCurrentRowHash: ""
        Component.onCompleted: {
            model.modelAboutToBeReset.connect(storeSelection)
            model.modelReset.connect(restoreSelection)
            restoreSelection()
        }
        function rowHash(row) {
            const index = clipboardItemView.index(row, clipboardItemModel.hashColumn)
            return clipboardItemModel.data(index)
        }
        function storeSelection() {
            lastCurrentRow = Math.max(0, clipboardItemView.currentRow)
            lastCurrentRowHash = rowHash(lastCurrentRow)
            while (lastCurrentRowHash === "" && lastCurrentRow < clipboardItemView.rows) {
                lastCurrentRow += 1
                lastCurrentRowHash = rowHash(lastCurrentRow)
            }
        }
        function restoreSelection() {
            var index = model.index(lastCurrentRow, 0)
            if (lastCurrentRowHash !== "") {
                while (index.row >= 0 && lastCurrentRowHash != rowHash(index.row)) {
                    index = model.index(index.row + 1, 0)
                }
                if (index.row < 0) {
                    index = model.index(lastCurrentRow, 0)
                    while (index.row >= 0 && lastCurrentRowHash != rowHash(index.row)) {
                        index = model.index(index.row - 1, 0)
                    }
                }
            }
            clipboardItemView.selectionModel.setCurrentIndex(index, ItemSelectionModel.Clear)
        }

        Menu {
            id: itemContextMenu

            // Copy item action
            MenuItem {
                text: qsTr("&Copy")
                icon.name: "edit-copy"
                enabled: clipboardItemView.currentRow >= 0
                onTriggered: clipboard.setData(clipboardItemView.currentData())
            }

            // Delete item action
            MenuItem {
                text: qsTr("&Delete")
                icon.name: "edit-delete"
                enabled: clipboardItemView.currentRow >= 0
                onTriggered: removeSelected()
            }
        }

        MouseArea {
            anchors.fill: parent
            acceptedButtons: Qt.RightButton
            onReleased: {
                var cell = clipboardItemView.cellAtPosition(mouseX, mouseY)
                var index = clipboardItemView.modelIndex(cell)
                var sel = clipboardItemView.selectionModel
                if (!sel.isSelected(index) && sel.currentIndex != index)
                    sel.setCurrentIndex(index, ItemSelectionModel.Clear)
                if (sel.currentIndex.row >= 0)
                    itemContextMenu.popup()
            }
        }

        // Copy item action
        Shortcut {
            sequence: 'Shift+Enter'
            onActivated: {
                view.hide()
                clipboard.setData(clipboardItemView.currentData())
            }
        }
        Shortcut {
            sequence: 'Shift+Return'
            onActivated: {
                view.hide()
                clipboard.setData(clipboardItemView.currentData())
            }
        }
        Shortcut {
            sequences: [StandardKey.Copy]
            onActivated: {
                clipboard.setData(clipboardItemView.currentData())
            }
        }

        // Paste or copy text
        Shortcut {
            sequence: 'Enter'
            onActivated: activateSelected()
        }
        Shortcut {
            sequence: 'Return'
            onActivated: activateSelected()
        }

        // Item context menu shortcut
        Shortcut {
            sequence: 'Menu'
            onActivated: {
                if (clipboardItemView.currentRow >= 0)
                    itemContextMenu.popup()
            }
        }

        Shortcut {
            sequences: [StandardKey.Delete]
            onActivated: removeSelected()
        }

        Shortcut {
            sequence: 'Escape'
            onActivated: {
                if (filterTextField.text == "") {
                  view.hide()
                } else {
                  filterTextField.text = ""
                  if (clipboardItemView.rows > 0) {
                      clipboardItemView.currentRow = -1
                      clipboardItemView.currentRow = 0
                  }
                }
            }
        }
    }

    // Quit/exit shortcut
    Shortcut {
        sequence: StandardKey.Quit
        context: Qt.ApplicationShortcut
        onActivated: Qt.quit()
    }

    // Filter/search/find shortcut
    Shortcut {
        sequence: StandardKey.Find
        context: Qt.ApplicationShortcut
        onActivated: filterTextField.focus = true
    }

    function activateSelected() {
        view.hide()
        var data = clipboardItemView.currentData()
        var text = data["text/plain"]
        if (!text || !paster || !paster.paste(text)) {
            clipboard.setData(data)
        }
    }

    function removeSelected() {
        var sel = clipboardItemView.selectionModel
        if (sel.selection.length == 0) {
            clipboardItemModel.removeItems(sel.currentIndex.row, 1)
        } else {
            while (sel.selection.length > 0) {
                const range = sel.selection[0]
                clipboardItemModel.removeItems(range.top, range.height)
            }
        }
    }
}
