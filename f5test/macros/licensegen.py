#!/usr/bin/env python
'''
Created on Apr 15, 2012

@author: jono
'''
from f5test.macros.base import Macro
from f5test.base import Options
from f5test.interfaces.selenium import SeleniumInterface
from f5test.interfaces.selenium.driver import By
import getpass
import logging
import pprint

__version__ = '0.2'
LOG = logging.getLogger(__name__)

BANNED_FEATURES = set(('Appliance Mode', 'TrustedIP Subscription', 
                       'IP Intelligence Subscription'))

MAP = Options()
MAP.eval = {}
MAP.eval.bigip = {}
MAP.eval.bigip['VE'] = 'F5-BIG-LTM-VE-1G-LIC'
MAP.eval.bigip['1600'] = 'F5-BIG-LTM-1600-4G-LIC'
MAP.eval.bigip['3600'] = 'F5-BIG-LTM-3600-4G-LIC'
MAP.eval.bigip['3900'] = 'F5-BIG-LTM-3900-8G-LIC'
MAP.eval.bigip['6400'] = 'F5-BIG-LTM-6400-LIC'
MAP.eval.bigip['6800'] = 'F5-BIG-LTM-6800-LIC'
MAP.eval.bigip['6900'] = 'F5-BIG-LTM-6900-8G-LIC'
MAP.eval.bigip['8400'] = 'F5-BIG-LTM-8400-LIC'
MAP.eval.bigip['8800'] = 'F5-BIG-LTM-8800-LIC'
MAP.eval.bigip['8900'] = 'F5-BIG-LTM-8900-LIC'
MAP.eval.bigip['8950'] = 'F5-BIG-LTM-8950-LIC'
MAP.eval.bigip['11000'] = 'F5-BIG-LTM-11000-48G-LIC'
MAP.eval.bigip['11050'] = 'F5-BIG-LTM-11050-LIC'
MAP.eval.bigip['C2400'] = 'F5-VPR-LTM-C2400-AC-LIC'
MAP.eval.bigip['C4400'] = 'F5-VPR-LTM-C4400-AC-LIC'
MAP.eval.em = {}
MAP.eval.em['VE'] = 'F5-EM-VE-LIC'
MAP.eval.em['3000'] = 'F5-EM-3000-LIC'
MAP.eval.em['4000'] = 'F5-EM-4000-LIC'

MAP.dev = {}
MAP.dev.bigip = {}
MAP.dev.bigip['VE'] = 'F5-BIG-LTM-VE-1G-LIC-DEV'
MAP.dev.bigip['1600'] = 'F5-BIG-LTM-1600-4G-DEV'
MAP.dev.bigip['3600'] = 'F5-BIG-LTM-3600-4G-DEV'
MAP.dev.bigip['3900'] = 'F5-BIG-LTM-3900-4G-DEV'
MAP.dev.bigip['6400'] = 'F5-BIG-LTM-6400-LIC-DEV'
MAP.dev.bigip['6800'] = 'F5-BIG-LTM-6800-LIC-DEV'
MAP.dev.bigip['6900'] = 'F5-BIG-LTM-6900-8G-LIC-DEV'
MAP.dev.bigip['8400'] = 'F5-BIG-LTM-8400-LIC-DEV'
MAP.dev.bigip['8800'] = 'F5-BIG-LTM-8800-LIC-DEV'
MAP.dev.bigip['8900'] = 'F5-BIG-LTM-8900-LIC-DEV'
MAP.dev.bigip['8950'] = 'F5-BIG-LTM-8950-LIC-DEV'
MAP.dev.bigip['11000'] = 'F5-BIG-LTM-11000-48G-LIC-DEV'
MAP.dev.bigip['11050'] = 'F5-BIG-LTM-11050-LIC-DEV'
MAP.dev.bigip['C2400'] = 'F5-VPR-LTM-C2400-AC-LIC-DEV'
MAP.dev.bigip['C4400'] = 'F5-VPR-LTM-C4400-AC-LIC-DEV'
MAP.dev.em = {}
MAP.dev.em['VE'] = 'F5-EM-VE-LIC-DEV'
MAP.dev.em['3000'] = 'F5-EM-3000-LIC-DEV'
MAP.dev.em['4000'] = 'F5-EM-4000-LIC-DEV'


class LicenseGenerator(Macro):

    def __init__(self, options, ifc=None):
        self.options = Options(options.__dict__)
        self.ifc = ifc
        self._ourifc = False

        super(LicenseGenerator, self).__init__()

    def prep(self):
        if not self.ifc:
            o = self.options
            self.ifc = SeleniumInterface(executor='http://%s:4444/wd/hub' % o.selenium,
                                         browser='htmlunit', platform='ANY')
            self.ifc.open()
            self._ourifc = True
        
    def cleanup(self):
        if self._ourifc:
            self.ifc.close()

    def setup(self):
        options = self.options
        b = self.ifc.api
        root = MAP.eval if self.options.eval else MAP.dev

        if self.options.bigip:
            productline = 'BIG-IP'
            product = root.bigip.get(options.bigip)
            if not product:
                pprint.pprint(root.bigip)
                raise ValueError("Only BIGIP %s are supported." % root.bigip.keys())
        elif self.options.em:
            productline = 'EM'
            product = root.em.get(options.em)
            if not product:
                pprint.pprint(root.em)
                raise ValueError("Only EM %s are supported." % root.em.keys())
        else:
            raise ValueError("Only BIGIP or EM are supported.")
        
        if self.options.eval:
            b.get('https://license.f5net.com/evalkeygenerator/')
        else:
            b.get('https://license.f5net.com/devkeygenerator/')
        
        LOG.info('Logging in...')
        e = b.find_element_by_name('user')
        e.send_keys(options.username)
        e = b.find_element_by_name('pass')
        e.send_keys(options.password)
        e = b.find_element_by_name('submit_form')
        select = e.click().wait('productline')
        
        LOG.info('SKU %s', product)
        LOG.info('Selecting product...')
        o = select.find_element_by_xpath("option[.='%s']" % productline)
        o.click()
        
        select = b.find_element_by_id('product')
        o = select.find_element_by_xpath("option[.='%s']" % product)
        o.click()
        
        if not self.options.eval:
            e = b.find_element_by_name('notes')
            e.send_keys('Generated using f5.licensegen v%s tool.' % __version__)

            e = b.find_element_by_name('eula_agree')
            e.click()

        button = b.find_element_by_id('nextBtn')
        table = button.click().wait('evalKeyTable')

        LOG.info('Selecting modules...')
        for e in table.find_elements_by_xpath("//tr/td[@class='productFont' "
                                              "and img[@src='images/assets/notSelectedBox.gif']]"):
            text = e.text.strip()
            if text.startswith('Access Policy Manager'):
                if not 'Max CCU' in text:
                    continue
            LOG.debug(text)
            img = e.find_element_by_tag_name('img')
            img.click()
        
        LOG.info('Selecting features...')
        for e in table.find_elements_by_xpath("//tr/td[@class!='productFont' "
                                              "and img[@src='images/assets/notSelectedBox.gif']]"):
            text = e.text.strip()
            for label in BANNED_FEATURES:
                banned = False
                if text.find(label) >= 0:
                    banned = True
                    break

            if not banned:
                LOG.debug(text)
                img = e.find_element_by_tag_name('img')
                img.click()

        LOG.info('Selecting radio buttons...')
        for e in table.find_elements_by_xpath("//tr[td='Multiple Options (please select one)']"
                                              "/following-sibling::tr[1]/td[1]"):
            text = e.text.strip()
            LOG.debug(text)
            img = e.find_element_by_tag_name('img')
            img.click()

        e = b.find_element_by_name('copier')
        e.clear()
        e.send_keys(str(options.count))

        button = table.find_element_by_css_selector("input[type=submit]")
        button.click().wait("//h1[.='SUCCESS - REQUEST PROCESSED']", by=By.XPATH)
        LOG.info('Done! You should receive an email shortly.')


def main():
    import optparse
    import sys

    usage = """%prog [options]"""

    formatter = optparse.TitledHelpFormatter(indent_increment=2, 
                                             max_help_position=60)
    p = optparse.OptionParser(usage=usage, formatter=formatter,
                            version="F5 License Generator v%s" % __version__
        )
    p.add_option("-v", "--verbose", action="store_true",
                 help="Debug messages")
    
    p.add_option("-c", "--count", metavar="INTEGER", default=1,
                 type="int", help="How many copies (default: 1)")
    p.add_option("-u", "--username", metavar="USERNAME",
                 type="string", help="Your OLYMPUS username.")
    p.add_option("-s", "--selenium", metavar="ADDRESS", default='localhost',
                 type="string", help="The selenium server address (default: localhost)")
    p.add_option("", "--bigip", metavar="PLATFORM",
                 type="string", help="The BIGIP platform (e.g.: 3900, VE, etc)")
    p.add_option("", "--em", metavar="PLATFORM",
                 type="string", help="The EM platform (e.g.: 4000, VE, etc)")
    p.add_option("", "--eval", action="store_true",
                 help="Generate Eval keys instead of Dev.")
    
    options, _ = p.parse_args()

    if options.verbose:
        level = logging.DEBUG
        logging.getLogger('selenium.webdriver.remote').setLevel(logging.INFO)
    else:
        level = logging.INFO
        logging.getLogger('f5test').setLevel(logging.INFO)
        logging.getLogger('f5test.macros').setLevel(logging.INFO)

    LOG.setLevel(level)
    logging.basicConfig(level=level)
    
    if not(options.bigip or options.em):
        p.print_version()
        p.print_help()
        sys.exit(2)

    if (options.bigip and options.em):
        raise ValueError("Either --bigip or --em not both.")

    options.password = getpass.getpass()
    
    cs = LicenseGenerator(options=options)
    cs.run()


if __name__ == '__main__':
    main()
