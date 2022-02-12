# SPDX-License-Identifier: LGPL-2.0-or-later
import QtQuick 2.0
import QtQuick.Controls 1.3

TextField {
    /// When text changes model.setFilterRegExp(text) is called.
    property QtObject model: null

    placeholderText: qsTr("Filter items")
    onTextChanged: {
        if (model) {
            model.filterCaseSensitivity = Qt.CaseInsensitive
            model.setFilterRegExp(text)
        }
    }
}
