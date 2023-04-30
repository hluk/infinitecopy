# SPDX-License-Identifier: LGPL-2.0-or-later
from PySide6.QtCore import QTimer
from PySide6.QtGui import QAccessible


def test_window_actite_at_start(app):
    qapp = app.app

    class Context:
        window = None
        focusObject = None

    timer = QTimer()
    timer.timeout.connect(qapp.quit)
    timer.start(5000)

    def changed():
        Context.window = qapp.focusWindow()
        Context.focusObject = qapp.focusObject()
        timer.start(0)

    qapp.focusWindowChanged.connect(changed)
    app.exec()

    assert Context.window is not None
    assert Context.focusObject is not None
    accessible = QAccessible.queryAccessibleInterface(Context.focusObject)
    assert accessible
    assert accessible.text(QAccessible.Name) == "item list"
