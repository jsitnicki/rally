# Copyright 2014: Mirantis Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from __future__ import print_function

from rally.cli import cliutils
from rally.cli.commands import plugin


class InfoCommands(object):
    """[Deprecated since 0.1.1] Allows you to get quick doc of rally entities.

    """

    @cliutils.args("--query", dest="query", type=str, help="Search query.")
    def find(self, query):
        """Search for an entity that matches the query and print info about it.

        :param query: search query.
        """
        print("This command was deprecated, and will be removed in 0.2.0 use:")
        print("rally plugin show %s" % query)

        plugin.PluginCommands().show(query)
        return 1

    def list(self):
        """List main entities in Rally for which rally info find works.

        Lists task scenario groups, deploy engines and server providers.
        """
        print("This command was deprecated, and will be removed in 0.2.0 use:")
        print("rally plugin list")

        plugin.PluginCommands().list()
        return 1
