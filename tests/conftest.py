# SPDX-License-Identifier: LGPL-2.0-or-later
import logging
import os
import sys
import time
from subprocess import PIPE, Popen

from PySide6.QtCore import QDir
from pytest import fixture

from infinitecopy.__main__ import createApp, createDbPath, initApp, serverName
from infinitecopy.Client import Client
from infinitecopy.PluginManager import plugin_paths

SESSION = "__TEST{}__"
APP_SESSION = "__TESTAPP__"
_last_session_id = 0

DISABLE_AUTOADD_PLUGIN = """
from infinitecopy import Plugin


class DisableAutoAddPlugin(Plugin):
    def onClipboardChanged(self, _data):
        return False
"""

CLIENT_TIMEOUT_SECONDS = 10

CPULIMIT = os.getenv("CPULIMIT")
CPULIMIT_CLIENT = os.getenv("CPULIMIT_CLIENT")
CPULIMIT_ARGS = [
    "cpulimit",
    "--include-children",
    "--limit",
]

logger = logging.getLogger(__name__)


def wait_for_server(session):
    client = Client(log_states=False)
    retry = 20
    server_name = serverName(session)

    if CPULIMIT:
        interval = 0.1 * 100 / int(CPULIMIT)
    else:
        interval = 0.1

    while not client.connect(server_name):
        if retry == 0:
            assert False
            break
        time.sleep(interval)
        retry -= 1

    client.disconnect()


def terminate_server(session):
    client = Client(log_states=False)
    server_name = serverName(session)
    if client.connect(server_name):
        client.sendCommandName("quit")
        client.sendCommandEnd()
        client.waitForDisconnected()


@fixture
def server():
    global _last_session_id
    _last_session_id += 1
    session = SESSION.format(_last_session_id)
    initApp(session)

    path = createDbPath()
    try:
        os.remove(path)
    except FileNotFoundError:
        pass

    terminate_server(session)

    plugin_path = next(plugin_paths())
    plugin_dir = QDir(plugin_path)
    assert plugin_dir.mkpath(".")
    with open(plugin_dir.absoluteFilePath("disable_autoadd.py"), "w") as f:
        f.write(DISABLE_AUTOADD_PLUGIN)

    timeout = CLIENT_TIMEOUT_SECONDS
    client_prefix_args = []

    def run_client(*args, stdin=b""):
        args = [
            *client_prefix_args,
            sys.executable,
            "-m",
            "infinitecopy",
            "--session",
            session,
            *args,
        ]
        with Popen(args, stdin=PIPE, stdout=PIPE, stderr=PIPE) as proc:
            try:
                out, err = proc.communicate(input=stdin, timeout=timeout)
                if proc.returncode != 0:
                    raise RuntimeError(err)
                return out
            finally:
                proc.terminate()
                proc.wait()

    args = [sys.executable, "-m", "infinitecopy", "--session", session]

    if CPULIMIT or CPULIMIT_CLIENT:
        if CPULIMIT_CLIENT:
            print(f"Limiting client CPU to {CPULIMIT_CLIENT}%")
            timeout = timeout * 100 / int(CPULIMIT_CLIENT)
            client_prefix_args = [*CPULIMIT_ARGS, CPULIMIT_CLIENT]
        if CPULIMIT:
            print(f"Limiting server CPU to {CPULIMIT}%")
            timeout = timeout * 100 / int(CPULIMIT)
            args = [*CPULIMIT_ARGS, CPULIMIT, *args]
        print(f"Client timeout is {timeout} seconds")

    with Popen(args) as proc:
        try:
            wait_for_server(session)
            yield run_client
        finally:
            terminate_server(session)
            proc.terminate()
            proc.wait()


@fixture
def app():
    app = createApp(args=["--session", APP_SESSION])
    assert app is not None
    try:
        yield app
    finally:
        app.app.quit()
