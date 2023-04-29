// SPDX-License-Identifier: LGPL-2.0-or-later
import QtQml
import QtQuick

Item {
    id: delegate

    required property TableView view

    required property int index
    required property bool selected
    required property bool current

    property color baseTextColor: (current || selected) ? palette.highlightedText : palette.text

    implicitWidth: view.width
    implicitHeight: row.implicitHeight

    clip: true
    property var dataDict: itemData
    property string text: itemText
    property string html: itemHtml

    Accessible.focused: current
    Accessible.name: `row ${index + 1}`
    Accessible.description: text ? `text: ${text}` : (hasImage ? "image" : "")

    Rectangle {
        anchors.fill: parent
        color: {
            if (current) {
                palette.highlight
            } else if (selected) {
                palette.highlight
            } else if (view.alternatingRows && index % 2 !== 0) {
                palette.alternateBase
            } else {
                palette.base
            }
        }
        Behavior on opacity { SmoothedAnimation { velocity: 0.2 } }
    }

    MouseArea {
        anchors.fill: parent
        onDoubleClicked: clipboard.setData(dataDict)
        onClicked: {
            const index = view.model.index(delegate.index, 0)
            view.selectionModel.setCurrentIndex(
                index, ItemSelectionModel.Clear)
        }
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
            width: hasImage ? Math.min(sourceSize.width, delegate.parent.width - rowNumberText.width - createdTimeText.width - 3 * spacing) : 0
            fillMode: Image.PreserveAspectFit
        }

        ClipboardItemHtml {
            color: baseTextColor
            text: '[HTML] ' + html
            visible: html != ''
        }

        ClipboardItemText {
            color: baseTextColor
            text: delegate.text
            visible: html == ''
        }

        ClipboardItemCopyTime {
            id: createdTimeText
            text: createdTime ? new Date(createdTime) : ''
            color: Qt.tint(baseTextColor, "lightsteelblue")
        }
    }
}
