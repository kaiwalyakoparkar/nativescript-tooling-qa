# -*- coding: utf-8 -*-
"""
Test for `tns run ios` command with Angular apps (on simulator).
"""
# pylint: disable=invalid-name

import os

from nose.tools import timed

from core.base_test.tns_test import TnsTest
from core.utils.device.device import Device
from core.utils.device.device_manager import DeviceManager
from core.utils.wait import Wait
from core.utils.npm import Npm
from core.utils.file_utils import File, Folder
from core.settings import Settings
from core.settings.Settings import Simulators, IOS, TEST_RUN_HOME, AppName
from core.utils.device.simctl import Simctl
from products.nativescript.tns import Tns
from products.nativescript.tns_logs import TnsLogs
from data.templates import Template

APP_NAME = AppName.DEFAULT
APP_PATH = os.path.join(Settings.TEST_RUN_HOME, APP_NAME)
IMAGE_PATH = os.path.join(TEST_RUN_HOME, 'assets', 'runtime', 'ios', 'images', 'iPhoneXR_12')
ASSERT_TEXT = 'Tap the button'


class IOSRuntimeTests(TnsTest):
    plugin_path = os.path.join(TEST_RUN_HOME, 'assets', 'plugins', 'sample-plugin', 'src')

    @classmethod
    def setUpClass(cls):
        TnsTest.setUpClass()
        cls.sim = DeviceManager.Simulator.ensure_available(Simulators.DEFAULT)
        Simctl.uninstall_all(cls.sim)

    def tearDown(self):
        TnsTest.tearDown(self)

    @classmethod
    def tearDownClass(cls):
        TnsTest.tearDownClass()
        Folder.clean(os.path.join(TEST_RUN_HOME, APP_NAME))

    @timed(360)
    def test_201_test_init_mocha_js_stacktrace(self):
        # https://github.com/NativeScript/ios-runtime/issues/565
        Tns.create(app_name=APP_NAME, template=Template.HELLO_WORLD_JS.local_package, update=True)
        Npm.install(package='mocha', folder=APP_PATH)
        Tns.platform_add_ios(APP_NAME, framework_path=IOS.FRAMEWORK_PATH)
        Tns.exec_command("test init --framework", cwd=APP_PATH, platform='mocha')

        File.copy(os.path.join(TEST_RUN_HOME, 'assets', 'runtime', 'ios', 'files', 'ios-runtime-565', 'example.js'),
                  os.path.join(APP_PATH, 'app', 'tests'))

        result = File.read(os.path.join(APP_PATH, 'app', 'tests', 'example.js'))
        assert "Mocha test" in result
        assert "Test" in result
        assert "Array" not in result

        result = Tns.exec_command("test ios", cwd=APP_PATH, emulator=True,
                                  log_trace=True, wait=False)
        strings = ['JavaScript stack trace', '@file:///app/tests/example.js:5:25']
        TnsLogs.wait_for_log(log_file=result.log_file, string_list=strings, timeout=90)

    def test_280_tns_run_ios_console_time(self):
        Tns.create(app_name=APP_NAME, template=Template.HELLO_WORLD_NG.local_package, update=True)
        Tns.platform_add_ios(APP_NAME, framework_path=IOS.FRAMEWORK_PATH)
        # Replace app.component.ts to use console.time() and console.timeEnd()

        File.copy(
            os.path.join(TEST_RUN_HOME, 'assets', 'runtime', 'ios', 'files', 'ios-runtime-843', 'app.component.ts'),
            os.path.join(APP_PATH, 'src', 'app', 'app.component.ts'))

        # `tns run ios` and wait until app is deployed
        result = Tns.run_ios(app_name=APP_NAME, emulator=True, wait=False, verify=False)

        # Verify initial state of the app
        strings = ['Project successfully built', 'Successfully installed on device with identifier', self.sim.id]
        TnsLogs.wait_for_log(log_file=result.log_file, string_list=strings, timeout=180, check_interval=10)

        Device.wait_for_text(self.sim, text="Ter Stegen", timeout=30)

        # Verify console.time() works - issue https://github.com/NativeScript/ios-runtime/issues/843
        console_time = ['CONSOLE INFO startup:']
        TnsLogs.wait_for_log(log_file=result.log_file, string_list=console_time)

    def test_290_tns_run_ios_console_dir(self):
        # NOTE: This test depends on creation of app in test_280_tns_run_ios_console_time
        # Replace app.component.ts to use console.time() and console.timeEnd()

        File.copy(
            os.path.join(TEST_RUN_HOME, 'assets', 'runtime', 'ios', 'files', 'ios-runtime-875', 'items.component.ts'),
            os.path.join(APP_PATH, 'src', 'app', 'item', 'items.component.ts'))

        # `tns run ios` and wait until app is deployed
        result = Tns.run_ios(app_name=APP_NAME, emulator=True, wait=False,
                             verify=False, log_trace=True)

        # Verify sync and initial state of the app
        strings = ['name: Ter Stegen', 'role: Goalkeeper', 'object dump end', self.sim.id]
        TnsLogs.wait_for_log(log_file=result.log_file, string_list=strings, timeout=90, check_interval=10)

    def test_380_tns_run_ios_plugin_dependencies(self):
        """
        issue https://github.com/NativeScript/ios-runtime/issues/890
        Check app is running when reference plugin A - plugin A depends on plugin B which depends on plugin C.
        Plugin A has dependency only to plugin B.
        Old behavior (version < 4.0.0) was in plugin A to reference plugin B and C.
        """

        Folder.clean(APP_NAME)
        Tns.create(APP_NAME, template=Template.HELLO_WORLD_JS.local_package)
        Tns.platform_add_ios(APP_NAME, framework_path=IOS.FRAMEWORK_PATH)

        # Add plugin with specific dependencies
        Tns.plugin_add(self.plugin_path, path=APP_NAME)

        # `tns run ios` and wait until app is deployed
        result = Tns.run_ios(app_name=APP_NAME, emulator=True, wait=False, verify=False)
        strings = ['Project successfully built', 'Successfully installed on device with identifier', self.sim.id]
        TnsLogs.wait_for_log(log_file=result.log_file, string_list=strings, timeout=150, check_interval=10)

        folder_path = os.path.join(APP_PATH, 'platforms', 'ios', APP_NAME, 'app',
                                   'tns_modules', 'nativescript-ui-core')
        assert Folder.exists(folder_path), "Cannot find folder: " + folder_path

        # Verify app is running on device
        Device.wait_for_text(self.sim, text=ASSERT_TEXT)

    def test_385_methods_with_same_name_and_different_parameters(self):
        """
        https://github.com/NativeScript/ios-runtime/issues/877
        PR https://github.com/NativeScript/ios-runtime/pull/1013
        """

        Folder.clean(APP_NAME)
        Tns.create(APP_NAME, template=Template.HELLO_WORLD_JS.local_package)
        Tns.platform_add_ios(APP_NAME, framework_path=IOS.FRAMEWORK_PATH)

        # Add plugin with specific dependencies
        Tns.plugin_add(self.plugin_path, path=APP_NAME)

        # Replace main-page.js to call methods with the same name but different parameters count
        File.copy(os.path.join(TEST_RUN_HOME, 'assets', 'runtime', 'ios', 'files', 'ios-runtime-877', 'main-page.js'),
                  os.path.join(APP_PATH, 'app', 'main-page.js'))

        result = Tns.run_ios(app_name=APP_NAME, emulator=True, wait=False, verify=False)
        strings = ['Project successfully built', 'Successfully installed on device with identifier', self.sim.id,
                   'SayName no param!', 'SayName with 1 param!', 'SayName with 2 params!']
        TnsLogs.wait_for_log(log_file=result.log_file, string_list=strings, timeout=150, check_interval=10)

        # Verify app is running on device
        Device.wait_for_text(self.sim, text=ASSERT_TEXT)

    def test_386_check_native_crash_will_not_crash_when_discardUncaughtJsExceptions_used(self):
        """
            Test native crash will not crash the app when discardUncaughtJsExceptions used
            https://github.com/NativeScript/ios-runtime/issues/1051
        """

        Folder.clean(APP_NAME)
        Tns.create(APP_NAME, template=Template.HELLO_WORLD_JS.local_package)
        Tns.platform_add_ios(APP_NAME, framework_path=IOS.FRAMEWORK_PATH)

        File.copy(os.path.join(TEST_RUN_HOME, 'assets', 'runtime', 'ios', 'files', 'ios-runtime-1051', 'app.js'),
                  os.path.join(APP_PATH, 'app', 'app.js'))
        File.copy(
            os.path.join(TEST_RUN_HOME, 'assets', 'runtime', 'ios', 'files', 'ios-runtime-1051', 'main-view-model.js'),
            os.path.join(APP_PATH, 'app', 'main-view-model.js'))
        # Change app package.json so it contains the options for discardUncaughtJsExceptions
        File.copy(os.path.join(TEST_RUN_HOME, 'assets', 'runtime', 'ios', 'files', 'ios-runtime-1051', 'package.json'),
                  os.path.join(APP_PATH, 'app', 'package.json'))

        log = Tns.run_ios(app_name=APP_NAME, emulator=True)

        strings = ['CONSOLE LOG file:///app/app.js:4:16: The folder “not-existing-path” doesn’t exist.',
                   'JS: 1   contentsOfDirectoryAtPathError@file:///app/main-view-model.js:6:47']

        test_result = Wait.until(lambda: all(string in File.read(log.log_file) for string in strings), timeout=300,
                                 period=5)

        # Verify app is running on device
        Device.wait_for_text(self.sim, text=ASSERT_TEXT)

        assert test_result, 'Native crash should not crash the app when discardUncaughtJsExceptions is used!'

    def test_387_test_pointers_and_conversions_to_string(self):
        """
            Test pointers and conversions to strings
            https://github.com/NativeScript/ios-runtime/pull/1069
            https://github.com/NativeScript/ios-runtime/issues/921
        """

        Folder.clean(APP_NAME)
        Tns.create(APP_NAME, template=Template.HELLO_WORLD_JS.local_package)
        Tns.platform_add_ios(APP_NAME, framework_path=IOS.FRAMEWORK_PATH)

        File.copy(os.path.join(TEST_RUN_HOME, 'assets', 'runtime', 'ios', 'files', 'ios-runtime-921', 'special-value',
                               'main-view-model.js'),
                  os.path.join(APP_PATH, 'app', 'main-view-model.js'))

        log = Tns.run_ios(app_name=APP_NAME, emulator=True)

        strings = ["<Pointer: 0xfffffffffffffffe>",
                   "<Pointer: 0xffffffffffffffff>",
                   "<Pointer: 0x800000000>"]

        test_result = Wait.until(lambda: all(string in File.read(log.log_file) for string in strings), timeout=300,
                                 period=5)
        assert test_result, '-1 pointer is not correct(interop.Pointer)!'

        File.copy(os.path.join(TEST_RUN_HOME, 'assets', 'runtime', 'ios', 'files', 'ios-runtime-921', 'wrapped-value',
                               'main-view-model.js'),
                  os.path.join(APP_PATH, 'app', 'main-view-model.js'))

        strings = ["wrapped: <Pointer: 0xfffffffffffffffe>",
                   "wrapped: <Pointer: 0xffffffffffffffff>",
                   "wrapped: <Pointer: 0x800000000>"]

        test_result = Wait.until(lambda: all(string in File.read(log.log_file) for string in strings), timeout=300,
                                 period=5)
        assert test_result, 'wrapped pointers are not working correctly(interop.Pointer(new Number(value)))!'

        File.copy(os.path.join(TEST_RUN_HOME, 'assets', 'runtime', 'ios', 'files', 'ios-runtime-921',
                               'toHexString-and-toDecimalString',
                               'main-view-model.js'),
                  os.path.join(APP_PATH, 'app', 'main-view-model.js'))

        strings = ["Hex: 0xfffffffffffffffe",
                   "Decimal: -2",
                   "Hex: 0xffffffffffffffff",
                   "Decimal: -1",
                   "Hex: 0x800000000",
                   "Decimal: 34359738368"]

        test_result = Wait.until(lambda: all(string in File.read(log.log_file) for string in strings), timeout=300,
                                 period=5)
        assert test_result, 'toHexString and toDecimalString are not working correctly!'