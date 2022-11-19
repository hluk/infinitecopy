// SPDX-License-Identifier: LGPL-2.0-or-later
import QtQuick
import QtQuick.Controls

TextField {
    property QtObject model: null

    placeholderText: qsTr("Filter items")
    onTextChanged: {
        if (model) {
            model.filterCaseSensitivity = Qt.CaseInsensitive
            model.filterRegularExpression = new RegExp(text)
        }
    }
}
