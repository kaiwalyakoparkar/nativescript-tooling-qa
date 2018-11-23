import logging
import os

from core.base_test.test_context import TestContext
from core.settings import Settings
from core.utils.file_utils import File
from core.utils.process import Run, Process
from core.utils.wait import Wait

NS_SCHEMATICS = "@nativescript/schematics"


class NG(object):

    @staticmethod
    def exec_command(command, wait=True):
        """
        Execute tns command.
        :param command: NG cli command.
        :param wait: Wait until command complete.
        :return: ProcessInfo object.
        :rtype: core.utils.process_info.ProcessInfo
        """
        cmd = '{0} {1}'.format(Settings.Executables.NG, command)
        return Run.command(cmd=cmd, wait=wait, log_level=logging.INFO)

    @staticmethod
    def new(collection=NS_SCHEMATICS, project=Settings.AppName.DEFAULT, shared=True, sample=False, prefix=None,
            source_dir=None, theme=True, style=None, webpack=True):
        """
        Execute `ng new`
        :param collection: Schematics collection.
        :param project: Project name.
        :param shared: If true pass --shared flag.
        :param sample: If true pass --sample flag.
        :param prefix: The prefix to apply to generated selectors (default value is `app`)
        :param source_dir: The name of the source directory (default value is `src`)
        :param theme: If false pass --no-theme flag.
        :param style: If style is not None pass --style flag (default value is `css`)
        :param webpack: If false pass --no-webpack flag.
        :return: ProcessInfo object.
        :rtype: core.utils.process_info.ProcessInfo
        """
        command = 'new'
        if collection is not None:
            command = command + ' --collection={0}'.format(collection)
        command = command + ' ' + project
        if shared:
            command = command + ' --shared'
        if sample:
            command = command + ' --sample'
        if prefix is not None:
            command = command + ' --prefix={0}'.format(str(prefix))
        if source_dir is not None:
            command = command + ' --sourceDir={0}'.format(str(source_dir))
        if style is not None:
            command = command + ' --style={0}'.format(str(style))
        if not webpack:
            command = command + ' --no-webpack'
        if not theme:
            command = command + ' --no-theme'

        TestContext.TEST_APP_NAME = project
        return NG.exec_command(command)

    @staticmethod
    def serve(project=Settings.AppName.DEFAULT, verify=True):
        """
        Execute `ng serve`
        :param project: Project name.
        :param verify: If true assert project compiled successfully.
        :return: ProcessInfo object.
        :rtype: core.utils.process_info.ProcessInfo
        """
        command = 'serve {0}'.format(os.path.join(Settings.TEST_RUN_HOME, project))
        result = NG.exec_command(command, wait=False)
        if verify:
            compiled = Wait.until(lambda: 'Compiled successfully' in File.read(result.log_file))
            assert compiled, 'Failed to compile NG app at {0}'.format(project)
        return result

    @staticmethod
    def kill():
        """
        Kill ng cli processes.
        """
        Process.kill_by_commandline(cmdline=Settings.Executables.NG)
