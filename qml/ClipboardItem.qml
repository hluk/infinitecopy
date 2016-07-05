import QtQuick 2.0

Item {
    id: delegate
    width: delegate.ListView.view.width
    height: row.height
    clip: true

    MouseArea {
        anchors.fill: parent
        onClicked: currentIndex = index
        onDoubleClicked: clipboard.text = itemText
    }

    Row {
        id: row
        spacing: 10

        ClipboardItemText {
            text: itemText || qsTr('<EMPTY>')
        }

        ClipboardItemCopyTime {
            text: copyTime || ''
        }
    }
}
