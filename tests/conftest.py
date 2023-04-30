# SPDX-License-Identifier: LGPL-2.0-or-later
import os
import sys
import time
from subprocess import Popen

from pytest import fixture

from infinitecopy.__main__ import createApp, createDbPath, initApp, serverName
from infinitecopy.Client import Client

SESSION = "__TEST__"
APP_SESSION = "__TESTAPP__"
last_session_id = 0


def wait_for_server():
    client = Client()
    retry = 20
    server_name = serverName(SESSION)
    while not client.connect(server_name):
        if retry == 0:
            assert False
            break
        time.sleep(0.1)
        retry -= 1
    client.disconnect()


@fixture(scope="session")
def server():
    initApp(SESSION)
    path = createDbPath()
    try:
        os.remove(path)
    except FileNotFoundError:
        pass

    def run_client(*args):
        app = createApp(args=["--session", SESSION, *args])
        assert app is None

    args = [sys.executable, "-m", "infinitecopy", "--session", SESSION]
    with Popen(args) as proc:
        try:
            wait_for_server()
            yield run_client
        finally:
            proc.terminate()
            proc.wait()


@fixture
def timer():
    return timer


@fixture
def app():
    app = createApp(args=["--session", APP_SESSION])
    assert app is not None
    try:
        yield app
    finally:
        app.app.quit()
