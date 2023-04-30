# SPDX-License-Identifier: LGPL-2.0-or-later
import importlib
import logging
import os
import sys
from inspect import isclass
from pathlib import Path

from PySide6.QtCore import QStandardPaths

import infinitecopy.plugins.post
import infinitecopy.plugins.pre
from infinitecopy.Plugin import Plugin

logger = logging.getLogger(__name__)


def plugin_paths():
    for path in QStandardPaths.standardLocations(
        QStandardPaths.AppConfigLocation
    ):
        yield f"{path}/plugins"


def plugin_files():
    for path in plugin_paths():
        plugin_dir = Path(path)
        plugins = [f for f in plugin_dir.glob("*.py") if f.is_file()]

        if plugins:
            logger.debug("Loading plugins from: %s", path)
        else:
            logger.debug("No plugins found in: %s", path)

        for plugin in sorted(plugins):
            yield plugin


def plugin_modules():
    yield "pre", infinitecopy.plugins.pre

    for plugin in plugin_files():
        plugin_name = os.path.basename(plugin).rsplit(".", 1)[0]
        module_name = f"plugin.{plugin_name}"
        spec = importlib.util.spec_from_file_location(module_name, plugin)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        yield plugin, module

    yield "post", infinitecopy.plugins.post


def load_plugins(app):
    for plugin, module in plugin_modules():
        try:
            if "setup" in module.__dict__:
                logger.debug("Loading plugin setup %s", plugin)
                module.setup(app)

            for name, obj in module.__dict__.items():
                if obj != Plugin and isclass(obj) and Plugin in obj.mro():
                    logger.debug("Loading plugin %s (%s)", name, plugin)
                    yield obj(app)
        except Exception as e:
            logger.warning("Failed to load plugin %s: %s", plugin, e)
            raise


class PluginManager:
    def __init__(self, app):
        self.app = app
        self.plugins = list(load_plugins(app))

    def onClipboardChanged(self, data):
        for plugin in self.plugins:
            if plugin.onClipboardChanged(data) is False:
                return

        self.app.clipboardItemModel.addItemNoEmpty(data)

    def onKeyEvent(self, event):
        for plugin in self.plugins:
            if plugin.onKeyEvent(event) is True:
                event.consumed = True
                return
