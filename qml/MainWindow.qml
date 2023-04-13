// SPDX-License-Identifier: LGPL-2.0-or-later
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ColumnLayout {
    Accessible.name: "infinitecopy main window"

    anchors.fill: parent

    FilterTextField {
        id: filterTextField

        Accessible.description: "filter items text field"

        Layout.fillWidth: true
        model: clipboardItemView.model

        KeyNavigation.tab: clipboardItemView
        KeyNavigation.down: clipboardItemView
    }

    ClipboardItemView {
        id: clipboardItemView

        Accessible.name: "item list"

        Layout.fillHeight: true
        Layout.fillWidth: true

        model: clipboardItemModelFilterProxy

        spacing: 10

        Menu {
            id: itemContextMenu

            // Copy item action
            MenuItem {
                text: qsTr("&Copy")
                icon.name: "edit-copy"
                enabled: clipboardItemView.currentIndex >= 0
                onTriggered: clipboard.setData(clipboardItemView.currentItem.dataDict)
            }

            // Delete item action
            MenuItem {
                text: qsTr("&Delete")
                icon.name: "edit-delete"
                enabled: clipboardItemView.currentIndex >= 0
                onTriggered: clipboardItemModel.removeItem(clipboardItemView.currentIndex)
            }
        }

        MouseArea {
            anchors.fill: parent
            acceptedButtons: Qt.RightButton
            onReleased: {
                clipboardItemView.currentIndex = clipboardItemView.indexAt(mouseX, mouseY)
                if (clipboardItemView.currentIndex >= 0)
                    itemContextMenu.popup()
            }
        }

        // Copy item action
        Shortcut {
            sequence: 'Shift+Enter'
            onActivated: {
                view.hide()
                clipboard.setData(clipboardItemView.currentItem.dataDict)
            }
        }
        Shortcut {
            sequence: 'Shift+Return'
            onActivated: {
                view.hide()
                clipboard.setData(clipboardItemView.currentItem.dataDict)
            }
        }
        Shortcut {
            sequences: [StandardKey.Copy]
            onActivated: {
                clipboard.setData(clipboardItemView.currentItem.dataDict)
            }
        }

        // Paste or copy text
        Shortcut {
            sequence: 'Enter'
            onActivated: {
                view.hide()
                if (!paster || !paster.paste(clipboardItemView.currentItem.text)) {
                    clipboard.setData(clipboardItemView.currentItem.dataDict)
                }
            }
        }
        Shortcut {
            sequence: 'Return'
            onActivated: {
                view.hide()
                if (!paster || !paster.paste(clipboardItemView.currentItem.text)) {
                    clipboard.setData(clipboardItemView.currentItem.dataDict)
                }
            }
        }

        // Item context menu shortcut
        Shortcut {
            sequence: 'Menu'
            onActivated: {
                if (clipboardItemView.currentIndex >= 0)
                    itemContextMenu.popup()
            }
        }

        // Down shortcut
        Shortcut {
            sequence: 'j'
            onActivated: {
                if (clipboardItemView.currentIndex + 1 < clipboardItemView.count)
                    clipboardItemView.currentIndex += 1
            }
        }

        // Up shortcut
        Shortcut {
            sequence: 'k'
            onActivated: {
                if (clipboardItemView.currentIndex > 0)
                    clipboardItemView.currentIndex -= 1
            }
        }

        Shortcut {
            sequence: 'Home'
            onActivated: {
                if (clipboardItemView.count > 0) {
                    clipboardItemView.currentIndex = -1
                    clipboardItemView.currentIndex = 0
                }
            }
        }

        Shortcut {
            sequence: 'End'
            onActivated: {
                if (clipboardItemView.count > 0) {
                    clipboardItemView.currentIndex = -1
                    clipboardItemView.currentIndex = clipboardItemView.count - 1
                }
            }
        }

        Shortcut {
            sequence: 'PgDown'
            onActivated: {
                if (clipboardItemView.count > 0) {
                    const y = clipboardItemView.contentY + clipboardItemView.height
                    var index = clipboardItemView.indexAt(0, y)
                    if (index == -1) {
                        index = clipboardItemView.indexAt(0, y + clipboardItemView.spacing)
                        if (index == -1) {
                            index = clipboardItemView.count - 1
                        }
                    }
                    clipboardItemView.currentIndex = index
                    clipboardItemView.positionViewAtIndex(index, ListView.Beginning)
                }
            }
        }

        Shortcut {
            sequence: 'PgUp'
            onActivated: {
                if (clipboardItemView.count > 0) {
                    const y = clipboardItemView.contentY
                    var index = clipboardItemView.indexAt(0, y)
                    if (index == -1) {
                        index = clipboardItemView.indexAt(0, y - clipboardItemView.spacing)
                        if (index == -1) {
                            index = clipboardItemView.count - 1
                        }
                    }
                    clipboardItemView.currentIndex = index
                    clipboardItemView.positionViewAtIndex(index, ListView.End)
                }
            }
        }

        Shortcut {
            sequences: [StandardKey.Delete]
            onActivated: {
                clipboardItemModel.removeItem(clipboardItemView.currentIndex)
            }
        }

        Shortcut {
            sequence: 'Escape'
            onActivated: {
                if (filterTextField.text == "") {
                  view.hide()
                } else {
                  filterTextField.text = ""
                  if (clipboardItemView.count > 0) {
                      clipboardItemView.currentIndex = -1
                      clipboardItemView.currentIndex = 0
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
}
