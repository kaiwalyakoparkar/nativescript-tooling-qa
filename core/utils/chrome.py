from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

from core.enums.os_type import OSType
from core.log.log import Log
from core.settings import Settings
from core.utils.process import Process


class Chrome(object):
    driver = None

    def __init__(self, kill_old=True):
        if kill_old:
            self.kill()
        path = ChromeDriverManager().install()
        Log.info('Starting Google Chrome ...')
        self.driver = webdriver.Chrome(executable_path=path)
        Log.info('Google Chrome started!')

    def open(self, url):
        self.driver.get(url)
        Log.info('Open url: ' + url)

    def kill(self, force=Settings.IS_ON_CI):
        """
        Kill Chrome browsers instance(s).
        :param force: If false it will kill only browsers started by driver.
        If true it will force kill all chrome processes.
        By default `force` is set to false on local machines and true on CI (when JENKINS_HOME variable is set).
        """
        if self.driver is not None:
            self.driver.quit()
        if force:
            if Settings.HOST_OS == OSType.OSX:
                Process.kill(proc_name='Google Chrome', proc_cmdline=None)
            else:
                Process.kill(proc_name="chrome", proc_cmdline=None)
            Process.kill(proc_name='chromedriver')
        Log.info('Kill Chrome browser!')