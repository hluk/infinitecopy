import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.3

ColumnLayout {
    anchors.fill: parent

    FilterTextField {
        id: filterTextField

        Layout.fillWidth: true
        model: clipboardItemView.model

        KeyNavigation.tab: clipboardItemView
        KeyNavigation.down: clipboardItemView
    }

    ClipboardItemView {
        id: clipboardItemView

        Layout.fillHeight: true
        Layout.fillWidth: true

        model: clipboardItemModelFilterProxy

        spacing: 10

        Menu {
            id: itemContextMenu

            // Copy item action
            MenuItem {
                text: qsTr("&Copy")
                shortcut: StandardKey.Copy
                iconName: "edit-copy"
                enabled: clipboardItemView.currentIndex >= 0
                onTriggered: clipboard.text = clipboardItemView.currentItem.text
            }

            // Delete item action
            MenuItem {
                text: qsTr("&Delete")
                shortcut: StandardKey.Delete
                iconName: "edit-delete"
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
