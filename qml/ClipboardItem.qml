// SPDX-License-Identifier: LGPL-2.0-or-later
import QtQuick 2.7

Item {
    id: delegate

    width: delegate.ListView.view.width
    height: row.height

    clip: true
    property var dataDict: itemData
    property string text: itemText
    property string html: itemHtml

    Rectangle {
        anchors.fill: parent
        color: index % 2 ? 'black' : 'transparent'
        opacity: currentIndex == index ? 0 : 0.05
        Behavior on opacity { SmoothedAnimation { velocity: 0.2 } }
    }

    MouseArea {
        anchors.fill: parent
        onClicked: currentIndex = index
        onDoubleClicked: clipboard.setData(dataDict)
    }

    Row {
        id: row
        spacing: 10
        padding: 5

        ClipboardItemRow {
            id: rowNumberText
            text: index + 1
        }

        Image {
            source: hasImage ? 'image://items/' + index : ''
            width: hasImage ? Math.min(sourceSize.width, delegate.parent.width - rowNumberText.width - copyTimeText.width - 3 * spacing) : 0
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
