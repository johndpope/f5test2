'''
Created on Jan 22, 2015

@author: jono
'''
import hashlib
import logging
import os
import re
import traceback
import xmlrpclib

from nose.case import Test
from urlparse import urljoin

from . import ExtendedPlugin, PLUGIN_NAME
from ...base import AttrDict
from ...interfaces.xmlrpc import BugzillaInterface
from .logcollect_start import CONTEXT_NAME


LOG = logging.getLogger(__name__)
URL = 'https://bugzilla.olympus.f5net.com/xmlrpc.cgi'
LOGIN = 'cloud_automation@f5.com'
PASSWORD = '2sJgHbvB'

# URL = 'http://mgmtdata.mgmt.pdsea.f5net.com/xmlrpc.cgi'
# LOGIN = 'i.turturica@f5.com'
# PASSWORD = 'f5site02'

DEFAULT_BRANCH = 'bigiq-mgmt'
DEFAULT_VERSION = 'Unspecified'
OPEN_BUG_STATES = ['New', 'Accepted', 'Reopened']
FOUND_BY = 'Test Automation'
BZ_KEYWORD = 'TestRunnerFailure'
REPRODUCIBLE = 'Always'
STATUS_NEW = 'NEW'
MAINTAINER = 'i.turturica@f5.com'
DEFAULT_RUN_TYPE = 'Adhoc'
BZ_REGEX = '((?:BZ|BUG)\s*(\d{6}))'


def isfail(cls, error_classes):
    if cls not in error_classes:
        return True
    _, _, isfail = error_classes[cls]
    return isfail


class Bugzilla(ExtendedPlugin):
    """
    Submit bugs on failures automatically.
    """
    enabled = False

    def options(self, parser, env):
        """Register commandline options."""
        parser.add_option('--with-bugzilla', action='store_true', default=False,
                          help="Enable Bugzilla bug reporting. (default: no)")

    def configure(self, options, noseconfig):
        super(Bugzilla, self).configure(options, noseconfig)
        from ...interfaces.testcase import ContextHelper
        self.data = ContextHelper().set_container(PLUGIN_NAME)
        self.enabled = noseconfig.options.with_bugzilla
        self.context = ContextHelper(CONTEXT_NAME)

        self.bzifc = BugzillaInterface(URL, LOGIN, PASSWORD, debug=0)
        self.blocking = set()

    def guess_component(self, test):
        o = self.options
        test_id = test.id()
        for pair in o.components:
            pattern, combo = pair.items().pop()
            if re.search(pattern, test_id):
                return combo.split('|', 1)
        raise ValueError('Unable to guess component for %s' % test_id)

    # Tested on: Bugzilla 4.4.1
    def file_or_update_bug(self, test, err, context=None):
        if re.search(BZ_REGEX, str(err[1]), flags=re.IGNORECASE):
            LOG.debug("Known issue found. Skipping Bugzilla reporting.")
            return

        if not isfail(err[0], self.data.test_result.errorClasses):
            LOG.debug("Not a failure. Skipping Bugzilla reporting.")
            return

        o = self.options
        dut = self.data.dut
        cfgifc = self.context.get_config()
        session = cfgifc.get_session()
        if isinstance(test, Test):
            author = getattr(test.test, 'author', o.default_asignee)
        else:
            author = o.default_asignee

        if context:
            test = context
        LOG.info("Looking for an existing bug(s)...")
        # Strip the first level off the test names which is the project name.
        test_name = test.id()[test.id().find('.') + 1:]
        summary = "BVT {}: {}".format(err[0].__name__, test_name)

        # Prepare variables used for substitution in the template text.
        var = AttrDict()
        var.harness = ''
        for dut in self.data.duts:
            var.harness += "{0.device} {0.platform} {0.version}\n".format(dut)
        var.url = session.get_url()
        # XXX: Assumes logcollect_start plugin ran before us.
        var.test_root = self.context.get_data('test_root')
        if var.test_root:
            var.test_url = urljoin(var.url + '/', os.path.basename(var.test_root))
        else:
            var.test_url = var.url
        var.config = cfgifc.api
        var.author = author
        var.traceback = ''.join(traceback.format_exception(*err))
        var.maintainer = MAINTAINER

        # Search for an existing OPEN bug first.
        payload = AttrDict()
        # payload.token = self.bzifc.token  # For Bugzilla 4.4.6+
        payload.version = o.version.get(dut.version.version, DEFAULT_VERSION)

        payload.status = OPEN_BUG_STATES
        # Using a hidden/unused custom field to store a hash that describes the
        # current test failure. We use this to do an exact match on subsequent
        # fails.
        # first_line = str(err[1]).split('\n')[0]
        exc_type = str(err[0])
        payload.cf_bzid_sea = hashlib.md5(summary + exc_type).hexdigest()

        ret = self.bzifc.api.Bug.search(dict(payload))
        if ret.bugs:
            TEMPLATE = "Re-occurred on harness:\n" \
                "{harness}\n" \
                "\n" \
                "{traceback}\n" \
                "Results: {url}\n"

            LOG.info("Found {}.".format(len(ret.bugs)))
            if len(ret.bugs) > 1:
                LOG.warning("More than one open BZ found!")
            payload = AttrDict()
            # payload.token = self.bzifc.token  # For Bugzilla 4.4.6+
            payload.id = ret.bugs[0].id
            payload.comment = TEMPLATE.format(**var)
            ret = self.bzifc.api.Bug.add_comment(dict(payload))
            LOG.info("Updated bug {}.".format(payload.id))
        else:
            TEMPLATE = "Test failed:\n"\
                "{harness}\n" \
                "\n" \
                "{traceback}\n"\
                "\n" \
                "Test owner: {author}\n" \
                "Results: {url}\n" \
                "This script is maintained by: {maintainer}"

            LOG.info("Creating a new bug...")
            # payload.token = self.bzifc.token  # For Bugzilla 4.4.6+
            payload.product, payload.component = self.guess_component(test)
            payload.status = STATUS_NEW
            payload.summary = summary
            payload.classification = o.classification
            payload.severity = o.severity
            payload.priority = o.priority
            payload.cf_branch = self.data.dut.get('project', DEFAULT_BRANCH)
            payload.url = session.get_url()
            payload.cc = o.cc
            payload.assigned_to = author
            payload.keywords = [BZ_KEYWORD]

            payload.description = TEMPLATE.format(**var)

            payload.cf_foundon = payload.version
            payload.cf_build = self.data.dut.version.build
            payload.cf_foundby = FOUND_BY
            payload.cf_reproducible = REPRODUCIBLE
            try:
                ret = self.bzifc.api.Bug.create(payload)
                LOG.info("Bug {} created.".format(ret.id))
            except xmlrpclib.Fault, e:
                LOG.error("Bugzilla failure: {}".format(e))

    def begin(self):
        self.bzifc.open()
        LOG.info('Logged in to Bugzilla successfully! user_id: %d', self.bzifc.user_id)

    def handleFailure(self, test, err):
        self.file_or_update_bug(test, err)

    def handleError(self, test, err):
        self.file_or_update_bug(test, err)

    def handleBlocked(self, test, err, context):
        # Report only once for a blocked context
        if context in self.blocking:
            return
        self.blocking.add(context)
        self.file_or_update_bug(test, err, context)

    def finalize(self, result):
        self.bzifc.close()
