import QtQuick 2.7

Item {
    id: delegate

    width: delegate.ListView.view.width
    height: row.height

    clip: true
    property string text: itemText

    MouseArea {
        anchors.fill: parent
        onClicked: currentIndex = index
        onDoubleClicked: clipboard.text = itemText
    }

    Row {
        id: row
        spacing: 10
        padding: 5

        ClipboardItemRow {
            text: index
        }

        ClipboardItemText {
            text: itemText || qsTr('<EMPTY>')
        }

        ClipboardItemCopyTime {
            text: copyTime ? Date(copyTime) : ''
        }
    }
}
