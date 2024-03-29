// SPDX-License-Identifier: LGPL-2.0-or-later
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

TextField {
    property QtObject model: null

    placeholderText: qsTr("Filter items")
    onTextChanged: {
        if (model) {
            model.textFilter = text
        }
    }
}
