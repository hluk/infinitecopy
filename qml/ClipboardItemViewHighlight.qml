// SPDX-License-Identifier: LGPL-2.0-or-later
import QtQuick 2.0

// Selection hightlight for current item in ListView
Rectangle {
    property ListView parentListView: undefined

    color: "#bdf"
    width: parentListView.currentItem ? parentListView.currentItem.width : 0
    height: parentListView.currentItem ? parentListView.currentItem.height : 0
    y: parentListView.currentItem ? parentListView.currentItem.y : 0
    Behavior on y { SmoothedAnimation { duration: 100 } }
}
