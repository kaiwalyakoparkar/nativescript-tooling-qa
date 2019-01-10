import json
import os
import time

from core.log.log import Log
from core.utils.file_utils import File
from core.utils.run import run


# noinspection PyShadowingBuiltins
class Simctl(object):

    @staticmethod
    def __run_simctl_command(command, wait=True, timeout=60):
        command = '{0} {1}'.format('xcrun simctl', command)
        return run(cmd=command, wait=wait, timeout=timeout)

    # noinspection PyBroadException
    @staticmethod
    def __get_simulators():
        result = Simctl.__run_simctl_command(command='list --json devices')
        try:
            return json.loads(result.output)
        except ValueError:
            Log.error('Failed to parse json ' + os.linesep + result.output)
            return json.loads('{}')

    @staticmethod
    def start(simulator_info):
        if simulator_info.id is not None:
            Simctl.__run_simctl_command(command='boot {0}'.format(simulator_info.id))
            Simctl.wait_until_boot(simulator_info)
            return simulator_info
        else:
            raise Exception('Can not boot iOS simulator if udid is not specified!')

    @staticmethod
    def is_running(simulator_info):
        sims = Simctl.__get_simulators()['devices']['iOS {0}'.format(simulator_info.sdk)]
        for sim in sims:
            if sim['name'] == simulator_info.name and sim['state'] == 'Booted':
                # simctl returns Booted too early, so we will wait some untill service is started
                simulator_info.id = sim['udid']
                command = 'spawn {0} launchctl print system | grep com.apple.springboard.services'.format(
                    simulator_info.id)
                service_state = Simctl.__run_simctl_command(command=command)
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
        sims = Simctl.__get_simulators()['devices']['iOS {0}'.format(simulator_info.sdk)]
        for sim in sims:
            if sim['name'] == simulator_info.name:
                simulator_info.id = sim['udid']
                return simulator_info
        return False

    @staticmethod
    def stop_application(simulator_info, app_id):
        return Simctl.__run_simctl_command('terminate {0} {1}'.format(simulator_info.id, app_id))

    @staticmethod
    def install(simulator_info, path):
        result = Simctl.__run_simctl_command('install {0} {1}'.format(simulator_info.id, path))
        assert result.exit_code == 0, 'Failed to install {0} on {1}'.format(path, simulator_info.name)
        assert 'Failed to install the requested application' not in result.output, \
            'Failed to install {0} on {1}'.format(path, simulator_info.name)

    @staticmethod
    def uninstall(simulator_info, app_id):
        result = Simctl.__run_simctl_command('uninstall {0} {1}'.format(simulator_info.id, app_id))
        assert result.exit_code == 0, 'Failed to uninstall {0} on {1}'.format(app_id, simulator_info.name)
        assert 'Failed to uninstall the requested application' not in result.output, \
            'Failed to uninstall {0} on {1}'.format(app_id, simulator_info.name)

    @staticmethod
    def get_screen(id, file_path):
        File.delete(file_path)
        result = Simctl.__run_simctl_command('io {0} screenshot {1}'.format(id, file_path))
        assert result.exit_code == 0, 'Failed to get screenshot of {0}'.format(id)
        assert File.exists(file_path), 'Failed to get screenshot of {0}'.format(id)

    @staticmethod
    def erase(simulator_info):
        result = Simctl.__run_simctl_command('erase {0}'.format(simulator_info.id))
        assert result.exit_code == 0, 'Failed to erase {0}'.format(simulator_info.name)
        Log.info('Erase {0}.'.format(simulator_info.name))

    @staticmethod
    def erase_all():
        result = Simctl.__run_simctl_command('erase all')
        assert result.exit_code == 0, 'Failed to erase all iOS Simulators.'
        Log.info('Erase all iOS Simulators.')
