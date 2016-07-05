import QtQuick 2.0
import QtQuick.Controls 1.3

TextField {
    /// When text changes model.setFilterRegExp(text) is called.
    property QtObject model: null

    placeholderText: qsTr("Filter items")
    onTextChanged: model ? model.setFilterRegExp(text) : null
}
