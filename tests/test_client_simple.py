# SPDX-License-Identifier: LGPL-2.0-or-later
from pytest import raises

from infinitecopy.__main__ import createApp


def test_server_not_running():
    expected_error = "Start the application before using a command"
    with raises(SystemExit, match=expected_error):
        createApp(args=["--session", "__TESTX__", "show"])


def test_unknown_command(server):
    expected_error = "Error: Unknown message received: _bad_command_"
    with raises(RuntimeError, match=expected_error):
        assert server("_bad_command_") == b""
