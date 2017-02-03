import QtQuick 2.7

Item {
    id: delegate

    width: delegate.ListView.view.width
    height: row.height

    clip: true
    property string text: itemText
    property string html: itemHtml

    MouseArea {
        anchors.fill: parent
        onClicked: currentIndex = index
        onDoubleClicked: clipboard.text = text
    }

    Row {
        id: row
        spacing: 10
        padding: 5

        ClipboardItemRow {
            id: rowNumberText
            text: index
        }

        Image {
            source: "image://items/" + index
            width: Math.min(sourceSize.width, delegate.parent.width - rowNumberText.width - copyTimeText.width - 3 * spacing)
            fillMode: Image.PreserveAspectFit
        }

        ClipboardItemHtml {
            text: html
            visible: html != ''
        }

        ClipboardItemText {
            text: delegate.text
            visible: html == ''
        }

        ClipboardItemCopyTime {
            id: copyTimeText
            text: copyTime ? Date(copyTime) : ''
        }
    }
}
