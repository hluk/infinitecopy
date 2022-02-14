# SPDX-License-Identifier: LGPL-2.0-or-later
import pickle  # nosec


def serializeData(data):
    return pickle.dumps(data)  # nosec


def deserializeData(bytes_):
    try:
        # FIXME: Avoid using unsafe pickle.
        return pickle.loads(bytes_)  # nosec
    except EOFError:
        return {}
    except TypeError:
        return {}
