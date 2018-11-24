import os
import unittest

from core.base_test.tns_test import TnsTest
from core.enums.os_type import OSType
from core.enums.platform_type import Platform
from core.settings import Settings
from core.utils.device.device_manager import DeviceManager
from data.sync_helpers import SyncHelpers
from data.templates import Template
from products.nativescript.tns import Tns


class CLISmokeTests(TnsTest):
    js_app_name = Settings.AppName.DEFAULT + 'JS'
    js_source_project_dir = os.path.join(Settings.TEST_RUN_HOME, js_app_name)
    js_target_project_dir = os.path.join(Settings.TEST_RUN_HOME, 'data', 'temp', js_app_name)

    ng_app_name = Settings.AppName.DEFAULT + 'NG'
    ng_source_project_dir = os.path.join(Settings.TEST_RUN_HOME, ng_app_name)
    ng_target_project_dir = os.path.join(Settings.TEST_RUN_HOME, 'data', 'temp', ng_app_name)

    emu = None
    sim = None

    @classmethod
    def setUpClass(cls):
        TnsTest.setUpClass()

        # Boot emulator and simulator
        cls.emu = DeviceManager.Emulator.ensure_available(Settings.Emulators.DEFAULT)
        if Settings.HOST_OS == OSType.OSX:
            cls.sim = DeviceManager.Simulator.ensure_available(Settings.Simulators.DEFAULT)

        # Create JS app and copy to temp data folder
        Tns.create(app_name=cls.js_app_name, template=Template.HELLO_WORLD_JS.local_package, update=True)
        Tns.platform_add_android(app_name=cls.js_app_name, framework_path=Settings.Android.FRAMEWORK_PATH)
        if Settings.HOST_OS is OSType.OSX:
            Tns.platform_add_ios(app_name=cls.js_app_name, framework_path=Settings.IOS.FRAMEWORK_PATH)

        # Create NG app and copy to temp data folder
        Tns.create(app_name=cls.ng_app_name, template=Template.HELLO_WORLD_NG.local_package, update=True)
        Tns.platform_add_android(app_name=cls.ng_app_name, framework_path=Settings.Android.FRAMEWORK_PATH)
        if Settings.HOST_OS is OSType.OSX:
            Tns.platform_add_ios(app_name=cls.ng_app_name, framework_path=Settings.IOS.FRAMEWORK_PATH)

    def setUp(self):
        TnsTest.setUp(self)

    @classmethod
    def tearDownClass(cls):
        TnsTest.tearDownClass()

    def test_001_run_android_js(self):
        SyncHelpers.sync_hello_world_js(app_name=self.js_app_name, platform=Platform.ANDROID, device=self.emu)

    @unittest.skipIf(Settings.HOST_OS is not OSType.OSX, 'iOS tests can be executed only on macOS.')
    def test_002_run_ios_js(self):
        SyncHelpers.sync_hello_world_js(app_name=self.js_app_name, platform=Platform.IOS, device=self.sim)

    def test_100_run_android_ng(self):
        SyncHelpers.sync_hello_world_ng(app_name=self.ng_app_name, platform=Platform.ANDROID, device=self.emu,
                                        bundle=True)

    @unittest.skipIf(Settings.HOST_OS is not OSType.OSX, 'iOS tests can be executed only on macOS.')
    def test_101_run_ios_ng(self):
        SyncHelpers.sync_hello_world_ng(app_name=self.ng_app_name, platform=Platform.IOS, device=self.sim,
                                        bundle=True)

    def test_200_build_android_release(self):
        Tns.build_android(app_name=self.js_app_name, release=True, bundle=True, aot=True, uglify=True, snapshot=True)

    @unittest.skipIf(Settings.HOST_OS is not OSType.OSX, 'iOS tests can be executed only on macOS.')
    def test_200_build_ios_release(self):
        Tns.build_ios(app_name=self.js_app_name, release=True, for_device=True, bundle=True, aot=True, uglify=True)