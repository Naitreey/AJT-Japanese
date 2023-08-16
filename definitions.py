# Copyright: Ren Tatsumoto <tatsu at autistici.org> and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import requests
from aqt.editor import Editor

from .config_view import config_view as cfg
from .helpers.sakura_client import SakuraParisClient


class SakuraParisAnkiClient(SakuraParisClient):

    def add_definition(self, editor: Editor):
        """
        Interaction with Anki's editor.
        """
        from aqt.utils import tooltip
        if self._config.source not in editor.note:
            return tooltip(f"Note doesn't have field \"{self._config.source}\".")
        if not editor.note[self._config.source]:
            return tooltip(f"Field \"{self._config.source}\" is empty.")
        try:
            definition = self.fetch_def(editor.note[self._config.source])
        except requests.exceptions.ConnectionError:
            return tooltip("Connection error.")
        else:
            if definition:
                editor.note[self._config.destination] = definition
            else:
                return tooltip("Nothing found.")


# Entry point
##########################################################################

sakura_client = SakuraParisAnkiClient(cfg.definitions)
