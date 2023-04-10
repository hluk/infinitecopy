#!/usr/bin/env python
# SPDX-License-Identifier: LGPL-2.0-or-later
import argparse
import getpass
import logging
import os
import signal
import sys
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QDir, QStandardPaths

from infinitecopy import __version__
from infinitecopy.Application import Application, ApplicationError
from infinitecopy.Client import Client

APPLICATION_NAME = "InfiniteCopy"

logger = logging.getLogger(__name__)


def parseArguments(args=None):
    parser = argparse.ArgumentParser(
        description=QCoreApplication.translate(
            "main", "Simple clipboard manager"
        )
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"{APPLICATION_NAME} {__version__}",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=os.getenv("INFINITECOPY_DEBUG") == "1",
        help="Enable debug logs",
    )
    parser.add_argument(
        "--no-paste",
        action="store_true",
        default=os.getenv("INFINITECOPY_NO_PASTE") == "1",
        help="Disable pasting clipboard from the app",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logs",
    )
    parser.add_argument(
        QCoreApplication.translate("main", "commands"),
        nargs="*",
        help=QCoreApplication.translate(
            "main", "Commands to send to the application"
        ),
    )
    return parser.parse_args(args)


def createDbPath():
    dataPath = QStandardPaths.writableLocation(
        QStandardPaths.AppLocalDataLocation
    )
    if not QDir(dataPath).mkpath("."):
        raise SystemExit(f"Failed to create data directory {dataPath}")

    dbPath = Path(dataPath, "infinitecopy_items.sql")
    logger.info("Using item database %r", dbPath)
    return str(dbPath)


def setUpPaths(app):
    path = Path(__file__).parent
    qmlPath = Path(path, "qml")
    if not qmlPath.exists():
        path = path.parent
        qmlPath = Path(path, "qml")

    iconPath = Path(path, "infinitecopy.png")
    app.setIcon(str(iconPath))

    qml = str(Path(qmlPath, "MainWindow.qml"))
    app.setMainWindowQml(qml)


def handleClient(serverName, args):
    client = Client()
    if not client.connect(serverName):
        if args.commands:
            raise SystemExit("Start the application before using a command")
        return False

    client.send(args.commands or ["show"])
    return True


def main():
    # Force exit app on SIGINT.
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    args = parseArguments()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    elif args.verbose:
        logging.basicConfig(level=logging.INFO)

    serverName = f"{APPLICATION_NAME}_{getpass.getuser()}"
    if handleClient(serverName, args):
        return

    try:
        app = Application(
            name=APPLICATION_NAME,
            version=__version__,
            dbPath=createDbPath(),
            serverName=serverName,
            enable_pasting=not args.no_paste,
            args=sys.argv,
        )
    except ApplicationError as e:
        raise SystemExit(f"Failed to start app: {e}")

    setUpPaths(app)

    return app.exec_()


if __name__ == "__main__":
    main()
