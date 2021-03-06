import json
import os
import time

from core.log.log import Log
from core.utils.file_utils import File
from core.utils.process import Process
from core.utils.run import run
from core.utils.version import Version


class Simctl(object):

    @staticmethod
    def run_simctl_command(command, wait=True, timeout=60):
        command = '{0} {1}'.format('xcrun simctl', command)
        return run(cmd=command, wait=wait, timeout=timeout)

    # noinspection PyBroadException
    @staticmethod
    def __get_simulators():
        result = Simctl.run_simctl_command(command='list --json devices')
        try:
            return json.loads(result.output)
        except ValueError:
            Log.error('Failed to parse json ' + os.linesep + result.output)
            return json.loads('{}')

    # noinspection PyBroadException
    @staticmethod
    def get_max_runtime_version(version):
        # Parse runtimes
        result = Simctl.run_simctl_command(command='list --json runtimes')
        try:
            runtimes = json.loads(result.output)
        except ValueError:
            Log.error('Failed to parse json ' + os.linesep + result.output)
            return json.loads('{}')

        # Get max runtime version
        exact_sdk_version = None
        for runtime in runtimes['runtimes']:
            if str(version) in runtime['version'] and runtime['name'].startswith('iOS') and runtime['isAvailable']:
                exact_sdk_version = Version.get(runtime['version'])
        if exact_sdk_version is None:
            raise Exception('Can not find iOS SDK {0}'.format(version))

        return exact_sdk_version

    @staticmethod
    def __get_devices_by_version(version):
        exact_sdk_version = Simctl.get_max_runtime_version(version)
        devices = Simctl.__get_simulators()['devices']
        placeholder = 'iOS {0}'
        device_key = placeholder.format(exact_sdk_version)
        if device_key not in devices:
            placeholder_dash = placeholder.format(exact_sdk_version).replace(' ', '-').replace('.', '-')
            device_key = 'com.apple.CoreSimulator.SimRuntime.{0}'.format(placeholder_dash)
        return devices[device_key]

    @staticmethod
    def __get_availability(sim):
        available = False
        if 'availability' in sim:
            available = sim['availability'] == u'(available)'
        elif 'isAvailable' in sim:
            available = sim['isAvailable']
        return available

    @staticmethod
    def start(simulator_info):
        if simulator_info.id is not None:
            Simctl.run_simctl_command(command='boot {0}'.format(simulator_info.id))
            assert Simctl.wait_until_boot(simulator_info), 'Failed to boot "{0}".'.format(simulator_info.id)
            return simulator_info
        else:
            raise Exception('Can not boot iOS simulator if udid is not specified!')

    @staticmethod
    def is_running(simulator_info):
        for sim in Simctl.__get_devices_by_version(simulator_info.sdk):
            if sim['name'] == simulator_info.name and sim['state'] == 'Booted':
                # simctl returns Booted too early, so we will wait some untill service is started
                simulator_info.id = str(sim['udid'])
                command = 'spawn {0} launchctl print system | grep com.apple.springboard.services'.format(
                    simulator_info.id)
                service_state = Simctl.run_simctl_command(command=command)
                if "M   A   com.apple.springboard.services" in service_state.output:
                    Log.info('Simulator "{0}" booted.'.format(simulator_info.name))
                    return simulator_info
        return False

    @staticmethod
    def wait_until_boot(simulator_info, timeout=180):
        """
        Wait until iOS Simulator is up and running.
        :param simulator_info: SimulatorInfo object.
        :param timeout: Timeout until device is ready (in seconds).
        :return: SimulatorInfo object with defined id, otherwise - False.
        """
        booted = False
        start_time = time.time()
        end_time = start_time + timeout
        while not booted:
            time.sleep(2)
            booted = Simctl.is_running(simulator_info)
            if booted or time.time() > end_time:
                return booted
        return booted

    @staticmethod
    def is_available(simulator_info):
        for sim in Simctl.__get_devices_by_version(simulator_info.sdk):
            if sim['name'] == simulator_info.name and Simctl.__get_availability(sim):
                simulator_info.id = str(sim['udid'])
                return simulator_info
        return False

    @staticmethod
    def stop_application(simulator_info, app_id):
        return Simctl.run_simctl_command('terminate {0} {1}'.format(simulator_info.id, app_id))

    @staticmethod
    def stop_all(simulator_info):
        for app_id in Simctl.get_all_apps(simulator_info):
            Simctl.stop_application(simulator_info, app_id)

    @staticmethod
    def install(simulator_info, path):
        result = Simctl.run_simctl_command('install {0} {1}'.format(simulator_info.id, path))
        if result.exit_code != 0:
            # Since Xcode 10 sometimes xcrun simctl install fails first time (usually with iPhone X* devices).
            Log.info('Failed to install {0} on {1}.'.format(path, simulator_info.name))
            Log.info('Retry...')
            result = Simctl.run_simctl_command('install {0} {1}'.format(simulator_info.id, path))
            assert result.exit_code == 0, 'Failed to install {0} on {1}'.format(path, simulator_info.name)
            assert 'Failed to install the requested application' not in result.output, \
                'Failed to install {0} on {1}'.format(path, simulator_info.name)

    @staticmethod
    def uninstall(simulator_info, app_id):
        result = Simctl.run_simctl_command('uninstall {0} {1}'.format(simulator_info.id, app_id))
        assert result.exit_code == 0, 'Failed to uninstall {0} on {1}'.format(app_id, simulator_info.name)
        assert 'Failed to uninstall the requested application' not in result.output, \
            'Failed to uninstall {0} on {1}'.format(app_id, simulator_info.name)
        Log.info('Successfully uninstalled {0} from {1}'.format(app_id, simulator_info.id))

    @staticmethod
    def uninstall_all(simulator_info):
        Simctl.stop_all(simulator_info)
        for app_id in Simctl.get_all_apps(simulator_info):
            Simctl.uninstall(simulator_info, app_id)

    @staticmethod
    def get_screen(sim_id, file_path):
        File.delete(file_path)
        result = Simctl.run_simctl_command('io {0} screenshot {1}'.format(sim_id, file_path))
        assert result.exit_code == 0, 'Failed to get screenshot of {0}'.format(sim_id)
        assert File.exists(file_path), 'Failed to get screenshot of {0}'.format(sim_id)

    @staticmethod
    def erase(simulator_info):
        result = Simctl.run_simctl_command('erase {0}'.format(simulator_info.id))
        assert result.exit_code == 0, 'Failed to erase {0}'.format(simulator_info.name)
        Log.info('Erase {0}.'.format(simulator_info.name))

    @staticmethod
    def erase_all():
        result = Simctl.run_simctl_command('erase all')
        assert result.exit_code == 0, 'Failed to erase all iOS Simulators.'
        Log.info('Erase all iOS Simulators.')

    @staticmethod
    def get_all_apps(simulator_info):
        bundle_ids = []
        root = '~/Library/Developer/CoreSimulator/Devices/{0}'.format(simulator_info.id)
        shell = 'find {0}/data/Containers/Bundle/Application -maxdepth 3 | grep .app | grep Info.plist'.format(root)
        result = run(cmd=shell, timeout=30)
        for plist in result.output.splitlines():
            bundle_id = run(cmd='/usr/libexec/PlistBuddy -c "Print :CFBundleIdentifier" {0}'.format(plist)).output
            if '.' in bundle_id:
                bundle_ids.append(bundle_id)
        return bundle_ids

    @staticmethod
    def is_process_running(simulator_info, app_id):
        result = Simctl.run_simctl_command('spawn {0} launchctl list | grep \'{1}\''.format(simulator_info.id, app_id))
        is_running = result.exit_code == 0
        if not is_running:
            Log.info('Process {0} is not running !'.format(app_id))
        return is_running

    @staticmethod
    def get_log_file(device_id):
        command = 'spawn {0} log stream --level=default'.format(device_id)
        Process.kill_by_commandline(command)
        log_file = Simctl.run_simctl_command(command=command, wait=False).log_file
        if File.exists(log_file):
            Log.debug('Log of {0} redirected to {1}'.format(device_id, log_file))
            return log_file
        else:
            message = 'Failed to get logs of {0}'.format(device_id)
            Log.error(message)
            raise Exception(message)
