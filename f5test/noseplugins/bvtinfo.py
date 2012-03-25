'''
Created on Jun 15, 2011

@author: jono
'''
from __future__ import absolute_import
from nose.plugins.base import Plugin
import logging
from ..base import Options
import urllib
import urllib2
import f5test.commands.icontrol as ICMD
#import f5test.commands.shell as SCMD
from ..utils import Version

LOG = logging.getLogger(__name__)


class BVTInfo(Plugin):
    enabled = True
    name = "bvtinfo"
    score = 519

    def options(self, parser, env):
        """Register commandline options."""
        parser.add_option('--no-bvtinfo', action='store_true',
                          dest='no_bvtinfo', default=False,
                          help="Disable BVTInfo reporting. (default: no)")

    def configure(self, options, noseconfig):
        """ Call the super and then validate and call the relevant parser for
        the configuration file passed in """
        from f5test.interfaces.config import ConfigInterface

        Plugin.configure(self, options, noseconfig)
        self.options = options
        if options.no_bvtinfo:
            self.enabled = False
        self.config_ifc = ConfigInterface()
        if self.enabled:
            config = self.config_ifc.open()
            assert config.bvtinfo, "BVTInfo requested but no bvtinfo section found in the config. "
            "You can disable this plugin by passing --no-bvtinfo."

    def _get_duts_info(self):
        # XXX: Lock bit should be configurable at a higher level
        devices = [x for x in self.config_ifc.get_all_devices(lock=False) 
                     if 'no-bvtinfo-reporting' not in x.tags]
        if not devices:
            return
        
        ret = []
        for device in devices:
            info = Options()
            info.device = device
            try:
                info.platform = ICMD.system.get_platform(device=device)
                info.version = ICMD.system.get_version(device=device, build=True)
                v = ICMD.system.parse_version_file(device=device)
                info.project = v.get('project')
                info.edition = v.get('edition', '')
            except Exception, e:
                LOG.error("%s: %s", type(e), e)
                info.version = Version()
                info.platform = ''
            ret.append(info)
        return ret

    def finalize(self, result):
        LOG.info("Reporting results to BVTInfo...")

        config = self.config_ifc.open()
        bvtinfocfg = config.bvtinfo
        if config.testopia._testrun:
            result_url = bvtinfocfg.result_url % {'run_id': config.testopia._testrun}
        else:
            result_url = ''
        result_text = "Total: %d, Fail: %d, Err: %d, Skip: %d" % \
                        ( result.testsRun,
                          len(result.failures),
                          len(result.errors),
                          len(result.skipped))

        # Report each device
        for dut in self._get_duts_info():
            if not dut.version or not dut.platform:
                LOG.error("Can't submit results without version or platform.")
                continue

            if dut.version.product.is_bigip  and \
               dut.version < 'bigip 10.0.1':
                LOG.info("Skipping old version: %s." % dut.version)
                continue

            LOG.info('BVTInfo report for: %s...', dut.device)
            project = dut.project or dut.version.version
            if dut.edition.startswith('Hotfix'):
                project = '%s-%s' % (project, dut.edition.split()[1].lower())
    
            params = urllib.urlencode(dict(
                bvttool = bvtinfocfg.name,
                project = bvtinfocfg.get('project', project),
                buildno = bvtinfocfg.get('build', dut.version.build),
                test_pass = int(not len(result.failures) and not len(result.errors)),
                platform = dut.platform,
                result_url = result_url,
                result_text = result_text
            ))
    
            LOG.debug(params)
            opener = urllib2.build_opener()
            urllib2.install_opener(opener)
            try:
                f = opener.open(bvtinfocfg.url, params)
                data = f.read()
                f.close()
                LOG.info('BVTInfo result report successful: (%s)', data)
            except urllib2.HTTPError, e:
                LOG.error('BVTInfo result report failed: %s (%s)', e, e.read())
            except Exception, e:
                LOG.error('BVTInfo result report failed: %s', e)