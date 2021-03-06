from core.base_test.tns_test import TnsTest
from core.settings import Settings
from core.utils.device.adb import Adb
from core.utils.device.device_manager import DeviceManager


class TnsRunAndroidTest(TnsTest):
    emu = None

    @classmethod
    def setUpClass(cls):
        TnsTest.setUpClass()
        cls.emu = DeviceManager.Emulator.ensure_available(Settings.Emulators.DEFAULT)

    def setUp(self):
        TnsTest.setUp(self)
        Adb.open_home(self.emu.id)
        Adb.clear_logcat(self.emu.id)

    def tearDown(self):
        TnsTest.tearDown(self)

    @classmethod
    def tearDownClass(cls):
        TnsTest.tearDownClass()
