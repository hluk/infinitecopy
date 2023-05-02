# SPDX-License-Identifier: LGPL-2.0-or-later
from unittest.mock import patch


def test_add_get_item(server, capsys):
    server("add", "test1", "test2", "test3")
    captured = capsys.readouterr()
    assert (captured.out, captured.err) == ("", "")

    server("get", "0", "1", "2")
    captured = capsys.readouterr()
    assert (captured.out, captured.err) == ("test3\ntest2\ntest1", "")

    server("get", ",", "0", "1", "2")
    captured = capsys.readouterr()
    assert (captured.out, captured.err) == ("test3,test2,test1", "")

    server("get", r"\n\t", "0", "1", "2")
    captured = capsys.readouterr()
    assert (captured.out, captured.err) == ("test3\n\ttest2\n\ttest1", "")


def test_add_get_item_large(server, capsys):
    input = b"[TEST]" * 50000
    with patch("sys.stdin.buffer.read", return_value=input):
        server("add", "-")
    captured = capsys.readouterr()
    assert (captured.out, captured.err) == ("", "")

    server("get", "0")
    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == input.decode("utf-8")
