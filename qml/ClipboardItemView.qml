import QtQuick 2.0
import QtQuick.Controls 1.4

ListView {
    focus: true
    delegate: ClipboardItem {}
    highlight: ClipboardItemViewHighlight {}
}
