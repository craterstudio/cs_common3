from __future__ import absolute_import

import os
import sys


class DataHolder(object):

    def __init__(self, host, platform):
        self._host = host
        self._platform = platform
        self._plugin = self.register_plugin(host)

    @property
    def host(self):
        return self._host

    @property
    def platform(self):
        return self._platform

    @property
    def plugin(self):
        return self._plugin

    def register_plugin(self, host):
        pass

    # --------------------------------------------------------------------------

    def _validate_host(self, host):
        pass

    # --------------------------------------------------------------------------

    # temporary
    def sum_list(self, value):
        return sum(value)
