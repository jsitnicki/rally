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

""" Rally command: verify """

import json
import os

import six

from rally.cmd import cliutils
from rally.cmd.commands import use
from rally.cmd import envutils
from rally import consts
from rally import db
from rally import exceptions
from rally.i18n import _
from rally import objects
from rally.openstack.common import cliutils as common_cliutils
from rally.orchestrator import api
from rally.verification.verifiers.tempest import json2html


class VerifyCommands(object):
    """Test cloud with Tempest

    Set of commands that allow you to perform Tempest tests of
    OpenStack live cloud.
    """

    @cliutils.args("--deploy-id", dest="deploy_id", type=str, required=False,
                   help="UUID of a deployment.")
    @cliutils.args("--set", dest="set_name", type=str, required=False,
                   help="Name of tempest test set. Available sets: %s" % ", ".
                   join(consts.TEMPEST_TEST_SETS))
    @cliutils.args("--regex", dest="regex", type=str, required=False,
                   help="Regular expression of test.")
    @cliutils.args("--tempest-config", dest="tempest_config", type=str,
                   required=False,
                   help="User specified Tempest config file location")
    @cliutils.args("--no-use", action="store_false", dest="do_use",
                   help="Don't set new task as default for future operations")
    @envutils.with_default_deploy_id
    def start(self, set_name="smoke", deploy_id=None, regex=None,
              tempest_config=None, do_use=False):
        """Start set of tests.

        :param set_name: Name of tempest test set
        :param deploy_id: a UUID of a deployment
        :param regex: Regular expression of test
        :param tempest_config: User specified Tempest config file location
        """

        if regex:
            set_name = "full"
        if set_name not in consts.TEMPEST_TEST_SETS:
            print("Sorry, but there are no desired tempest test set. Please "
                  "choose from: %s" % ", ".join(consts.TEMPEST_TEST_SETS))
            return (1)
        verification = api.verify(deploy_id, set_name, regex, tempest_config)
        if do_use:
            use.UseCommands().verification(verification['uuid'])

    def list(self):
        """Display all verifications table, started and finished."""

        fields = ['UUID', 'Deployment UUID', 'Set name', 'Tests', 'Failures',
                  'Created at', 'Status']
        verifications = db.verification_list()
        if verifications:
            common_cliutils.print_list(verifications, fields,
                                       sortby_index=fields.index('Created at'))
        else:
            print(_("There are no results from verifier. To run a verifier, "
                    "use:\nrally verify start"))

    @cliutils.args('--uuid', type=str, dest='verification_uuid',
                   help='UUID of the verification')
    @cliutils.args('--html', action='store_true', dest='output_html',
                   help=('Results will be in html format'))
    @cliutils.args('--json', action='store_true', dest='output_json',
                   help=('Results will be in json format'))
    @cliutils.args('--output-file', type=str, required=False,
                   dest='output_file',
                   help='If specified, output will be saved to given file')
    @envutils.with_default_verification_id
    def results(self, verification_uuid=None, output_file=None,
                output_html=None, output_json=None):
        """Get raw results of the verification.

        :param verification_uuid: Verification UUID
        :param output_file: If specified, output will be saved to given file
        :param output_html: The output will be in HTML format
        :param output_json: The output will be in JSON format (Default)
        """

        try:
            results = db.verification_result_get(verification_uuid)['data']
        except exceptions.NotFoundException as e:
            print(six.text_type(e))
            return 1

        result = ''
        if len(filter(lambda x: bool(x), [output_json, output_html])) > 1:
            print("Please specify only one output format.")
        elif output_html:
            result = json2html.main(results)
        else:
            result = json.dumps(results, sort_keys=True, indent=4)

        if output_file:
            output_file = os.path.expanduser(output_file)
            with open(output_file, 'wb') as f:
                f.write(result)
        else:
            print(result)

    @cliutils.args('--uuid', dest='verification_uuid', type=str,
                   required=False,
                   help='UUID of a verification')
    @cliutils.args('--sort-by', dest='sort_by', type=str, required=False,
                   help='Tests can be sorted by "name" or "duration"')
    @cliutils.args('--detailed', dest='detailed', action='store_true',
                   required=False, help='Prints traceback of failed tests')
    @envutils.with_default_verification_id
    def show(self, verification_uuid=None, sort_by='name', detailed=False):
        """Display results table of the verification."""

        try:
            sortby_index = ('name', 'duration').index(sort_by)
        except ValueError:
            print("Sorry, but verification results can't be sorted "
                  "by '%s'." % sort_by)
            return 1

        try:
            verification = db.verification_get(verification_uuid)
            tests = db.verification_result_get(verification_uuid)
        except exceptions.NotFoundException as e:
            print(six.text_type(e))
            return 1

        print ("Total results of verification:\n")
        total_fields = ['UUID', 'Deployment UUID', 'Set name', 'Tests',
                        'Failures', 'Created at', 'Status']
        common_cliutils.print_list([verification], fields=total_fields)

        print ("\nTests:\n")
        fields = ['name', 'time', 'status']

        values = map(objects.Verification,
                     six.itervalues(tests.data['test_cases']))
        common_cliutils.print_list(values, fields, sortby_index=sortby_index)

        if detailed:
            for test in six.itervalues(tests.data['test_cases']):
                if test['status'] == 'FAIL':
                    formatted_test = (
                        '====================================================='
                        '=================\n'
                        'FAIL: %(name)s\n'
                        'Time: %(time)s\n'
                        'Type: %(type)s\n'
                        '-----------------------------------------------------'
                        '-----------------\n'
                        '%(log)s\n'
                    ) % {
                        'name': test['name'], 'time': test['time'],
                        'type': test['failure']['type'],
                        'log': test['failure']['log']}
                    print (formatted_test)

    @cliutils.args('--uuid', dest='verification_uuid', type=str,
                   required=False,
                   help='UUID of a verification')
    @cliutils.args('--sort-by', dest='sort_by', type=str, required=False,
                   help='Tests can be sorted by "name" or "duration"')
    @envutils.with_default_verification_id
    def detailed(self, verification_uuid=None, sort_by='name'):
        """Display results table of verification with detailed errors."""

        self.show(verification_uuid, sort_by, True)
