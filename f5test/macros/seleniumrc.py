#!/usr/bin/env python
'''
Created on Jun 3, 2011

@author: jono
'''
from f5test.macros.base import Macro
from f5test.base import Options
from f5test.interfaces.subprocess import ShellInterface
import os
import inspect
import time
import logging


DISPLAY = ':99'
SELENIUM_JAR = 'selenium-server-standalone.jar'
LOG = logging.getLogger(__name__)
__version__ = '0.2'


class SeleniumRC(Macro):

    def __init__(self, options, action):
        self.options = Options(options.__dict__)
        self.action = action

        if options.env:
            venv_dir = options.env
            bin_dir = os.path.join(venv_dir, 'bin')
        else:
            bin_dir = os.path.dirname(os.path.realpath(inspect.stack()[-1][1]))
            venv_dir = os.path.dirname(bin_dir)

        LOG.info('Using sandbox directory: %s', venv_dir)
        params = Options()
        params.display = options.display
        
        params.jar = os.path.join(bin_dir, SELENIUM_JAR)
        assert os.path.exists(params.jar), '%s not found' % params.jar
        
        var_run = os.path.join(venv_dir, 'var', 'run')
        var_log = os.path.join(venv_dir, 'var', 'log')
        if not os.path.exists(var_run):
            os.makedirs(var_run)
        
        if not os.path.exists(var_log):
            os.makedirs(var_log)
        
        params.xvfb_pid_file = os.path.join(var_run, 'xvfb.pid')
        params.xvfb_log_file = os.path.join(var_log, 'xvfb.log')
        params.sel2_pid_file = os.path.join(var_run, 'selenium.pid')
        params.sel2_log_file = os.path.join(var_log, 'selenium.log')
        
        self.params = params
        super(SeleniumRC, self).__init__()

    def do_kill_wait(self, pid, signal, timeout=10, interval=0.1):
        os.kill(pid, signal)
        now = start = time.time()
        
        while now - start < timeout:
            try:
                os.kill(pid, 0)
            except OSError:
                break
            
            time.sleep(interval)
            now = time.time()
        else:
            LOG.error('Timeout waiting for PID %d to finish.', pid)

    def stop(self):
        LOG.info('Action: %s', self.action)
        #with ShellInterface(timeout=self.options.timeout) as shell:
        params = self.params
        
        if os.path.exists(params.xvfb_pid_file):
            pid = int(open(params.xvfb_pid_file).read())
            LOG.info('Sending SIGTERM to Xvfb: %d', pid)
            try:
                self.do_kill_wait(pid, 15)
            finally:
                os.remove(params.xvfb_pid_file)
        
        if os.path.exists(params.sel2_pid_file):
            pid = int(open(params.sel2_pid_file).read())
            LOG.info('Sending SIGTERM to Selenium: %d', pid)
            try:
                self.do_kill_wait(pid, 15)
            finally:
                os.remove(params.sel2_pid_file)
        
    def start(self):
        LOG.info('Action: %s', self.action)
        
        with ShellInterface(timeout=self.options.timeout) as shell:
            params = self.params
            os.environ.update({'DISPLAY': params.display})
            env = os.environ
            is_remote = bool(params.display.split(':')[0])

            # Open the log file and leave it open so the process can still write
            # while it's running.
            if not self.options.no_xvfb and not is_remote:
                if not self.options.force and os.path.exists(params.xvfb_pid_file):
                    LOG.error('Selenium pid file exists: %s Stop first or use --force to override.', params.xvfb_pid_file)
                    return

                proc = shell.api.run('Xvfb -ac -extension GLX +render %(display)s -screen 0 1366x768x24' % params, 
                                     env=env, fork=True,
                                     stream=open(params.xvfb_log_file, 'w'))
                
                LOG.info('Xvfb pid: %d', proc.pid)
                with file(params.xvfb_pid_file, 'w') as f:
                    f.write(str(proc.pid))

            if not self.options.no_selenium:
                if not self.options.force and os.path.exists(params.sel2_pid_file):
                    LOG.error('Selenium pid file exists: %s. Stop first or use --force to override.', params.sel2_pid_file)
                    return

                proc = shell.api.run('java -jar %(jar)s' % params, 
                                     env=env, fork=True, 
                                     stream=open(params.sel2_log_file, 'w'))
                
                LOG.info('Selenium pid: %d', proc.pid)
                with file(params.sel2_pid_file, 'w') as f:
                    f.write(str(proc.pid))
        
    def setup(self):
        if self.action == 'start':
            return self.start()
        elif self.action == 'stop':
            return self.stop()
        elif self.action == 'restart':
            self.stop()
            self.start()
        else:
            ValueError('Unknown action: %s' % self.action)


def main():
    import optparse
    import sys

    usage = """%prog [options] <action>"""

    formatter = optparse.TitledHelpFormatter(indent_increment=2, 
                                             max_help_position=60)
    p = optparse.OptionParser(usage=usage, formatter=formatter,
                            version="Selenium RC Tool v%s" % __version__
        )
    p.add_option("-v", "--verbose", action="store_true",
                 help="Debug messages")
    
    p.add_option("-d", "--display", metavar="DISPLAY",
                 default=DISPLAY, type="string",
                 help="The display to be used (default: %s)" % DISPLAY)
    p.add_option("-e", "--env", metavar="DIRECTORY", type="string",
                 help="The sandbox directory (default: .)")
    p.add_option("-t", "--timeout", metavar="TIMEOUT", type="int", default=60,
                 help="Timeout. (default: 60)")
    p.add_option("", "--no-xvfb", action="store_true",
                 help="Don't start Xvfb.")
    p.add_option("", "--no-selenium", action="store_true",
                 help="Don't start Selenium Server.")
    p.add_option("", "--force", action="store_true",
                 help="Overwrite pid files.")

    options, args = p.parse_args()

    if options.verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
        #logging.getLogger('paramiko.transport').setLevel(logging.ERROR)
        logging.getLogger('f5test').setLevel(logging.ERROR)
        logging.getLogger('f5test.macros').setLevel(logging.INFO)

    LOG.setLevel(level)
    logging.basicConfig(level=level)
    
    if not args or args[0] not in ('start', 'stop', 'restart'):
        p.print_version()
        p.print_help()
        sys.exit(2)
    
    cs = SeleniumRC(options=options, action=args[0])
    cs.run()


if __name__ == '__main__':
    main()
