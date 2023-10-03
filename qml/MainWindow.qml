// SPDX-License-Identifier: LGPL-2.0-or-later
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import InfiniteCopy 1.0

ColumnLayout {
    Accessible.name: "infinitecopy main window"

    anchors.fill: parent

    RowLayout {
        z: 2

        FilterTextField {
            id: filterTextField
            Accessible.description: "filter items text field"

            Layout.fillWidth: true
            model: clipboardItemModel

            KeyNavigation.tab: clipboardItemView
            KeyNavigation.down: clipboardItemView
        }

        ComboBox {
            textRole: "text"
            model: ListModel {
                id: items
                ListElement { text: qsTr("smart-case"); value: ClipboardItemModel.CaseSensitivity.Smart }
                ListElement { text: qsTr("case-sensitive"); value: ClipboardItemModel.CaseSensitivity.Sensitive }
                ListElement { text: qsTr("ignore-case"); value: ClipboardItemModel.CaseSensitivity.Ignore }
            }
            onCurrentIndexChanged: {
                clipboardItemModel.caseSensitivity = items.get(currentIndex).value
            }
        }
    }

    ClipboardItemView {
        id: clipboardItemView
        z: 1

        Accessible.name: "item list"

        Layout.fillHeight: true
        Layout.fillWidth: true

        model: clipboardItemModel

        // Keep a row selected after list updates.
        property int lastCurrentRow: 0
        property string lastCurrentRowHash: ""
        Component.onCompleted: {
            model.modelAboutToBeReset.connect(storeSelection)
            model.modelReset.connect(restoreSelection)
            restoreSelection()
        }
        function rowHash(row) {
            const index = clipboardItemView.index(row, 0)
            return clipboardItemModel.data(index, clipboardItemModel.itemHashRole)
        }
        function storeSelection() {
            lastCurrentRow = Math.max(0, clipboardItemView.currentRow)
            if (lastCurrentRow === 0) {
                lastCurrentRowHash = ""
            } else {
                lastCurrentRowHash = rowHash(lastCurrentRow) || ""
                // If hash is not available, assume that selection was removed
                // and select the new item in the row at the start of the
                // removed selection.
                if (lastCurrentRowHash === "") {
                    const sel = clipboardItemView.selectionModel.selection
                    lastCurrentRow = sel[0] ? sel[0].top : 0
                }
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
                      const index = clipboardItemView.model.index(0, 0)
                      clipboardItemView.selectionModel.setCurrentIndex(
                          index, ItemSelectionModel.Clear)
                  }
                }
            }
        }

        Shortcut {
            sequence: 'Home'
            onActivated: {
                const index = clipboardItemView.model.index(0, 0)
                clipboardItemView.selectionModel.setCurrentIndex(
                    index, ItemSelectionModel.Clear)
                clipboardItemView.positionViewAtRow(0, Qt.AlignVertical_Mask)
            }
        }

        Shortcut {
            sequence: 'End'
            onActivated: {
                const row = clipboardItemView.model.rowCount() - 1
                const index = clipboardItemView.model.index(row, 0)
                clipboardItemView.selectionModel.setCurrentIndex(
                    index, ItemSelectionModel.Clear)
                clipboardItemView.positionViewAtRow(row, Qt.AlignVertical_Mask)
                console.log(row, clipboardItemView.model.rowCount() - 1)
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
