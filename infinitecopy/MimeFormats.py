# SPDX-License-Identifier: LGPL-2.0-or-later
from PySide6.QtCore import QByteArray

mimeText = "text/plain"
mimeHtml = "text/html"
mimePng = "image/png"
mimeSvg = "image/svg"

mimePrefixInternal = "application/x-infinitcopy-"
mimePrefixUser = "application/x-infinitcopyuser-"

mimeOwner = f"{mimePrefixInternal}owner"

mimeSource = f"{mimePrefixInternal}source"
valueSourceClipboard = QByteArray(b"clipboard")
valueSourceSelection = QByteArray(b"selection")
