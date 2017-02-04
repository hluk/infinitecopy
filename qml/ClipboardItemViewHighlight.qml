import QtQuick 2.0

// Selection hightlight for current item in ListView
Rectangle {
    property ListView parentListView: undefined

    color: "#bdf"
    width: parentListView.currentItem.width
    height: parentListView.currentItem.height
    y: parentListView.currentItem.y
    Behavior on y { SmoothedAnimation { duration: 100 } }
}