# SPDX-License-Identifier: LGPL-2.0-or-later
def test_add_get_item_multiple(server):
    assert server("add", "test1", "test2", "test3") == b""
    assert server("count") == b"3"
    assert server("get", "0", "1", "2") == b"test3\ntest2\ntest1"
    assert server("get", ",", "0", "1", "2") == b"test3,test2,test1"
    assert server("get", r"\n\t", "0", "1", "2") == b"test3\n\ttest2\n\ttest1"


def test_add_get_item_large(server):
    expected = b"[TEST]" * 50000
    assert server("add", "-", stdin=expected) == b""
    assert server("count") == b"1"
    item = server("get", "0")
    # Try to avoid printing a huge diff on failure.
    assert item[:20] == expected[:20]
    assert len(item) == len(expected)
    assert item == expected
