# SPDX-License-Identifier: LGPL-2.0-or-later
import QtQuick 2.0
import QtQuick.Controls 1.4

ListView {
    id: listView
    focus: true
    delegate: ClipboardItem {}

    // Custom item selection highlight.
    highlightFollowsCurrentItem: false
    highlight: ClipboardItemViewHighlight {
        parentListView: listView
    }
}
