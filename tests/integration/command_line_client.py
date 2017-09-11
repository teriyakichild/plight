from subprocess import Popen, PIPE, CalledProcessError

from logging import DEBUG, ERROR
import logging


class CommandLineResponse(object):
    """Bare bones object for any Command Line Connector response"""
    def __init__(self):
        super(CommandLineResponse, self).__init__()
        self.command = ""
        self.standard_out = []
        self.standard_error = []
        self.return_code = None
        self.process = None


class CommandLineClient(object):
    """
    Provides low level connectivity to the commandline via popen()

    Primarily intended to serve as base classes for a specific command line
    client Class. This class is dependent on a local installation of the
    wrapped client process. The thing you run has to be there!
    """

    def __init__(self, base_command):
        """
        :param base_command: This shell command to execute, e.g. 'ls' or 'pwd'
        """

        super(CommandLineClient, self).__init__()
        self.base_command = base_command
        self.root_log = logging.getLogger()

    def _build_command(self, cmd, *args):
        # Process command we received
        command = "{0} {1}".format(
            self.base_command, cmd) if self.base_command else cmd
        argstring = " ".join(args)
        command = "{0} {1}".format(command, argstring)
        return command

    def _execute_command(self, command):
        # Run the command
        process = None
        try:
            process = Popen(command, stdout=PIPE, stderr=PIPE, shell=True)
        except CalledProcessError as exception:
            self._log.exception(
                "Exception running commandline command {0}\n{1}".format(
                    str(command), str(exception)))
        return process

    def run_command_async(self, cmd, *args):
        """Running a command asynchronously returns a CommandLineResponse
        objecct with a running subprocess.Process object in it.  This process
        needs to be closed or killed manually after execution."""

        response = CommandLineResponse()
        response.command = self._build_command(cmd, *args)
        response.process = self._execute_command(response.command)
        return response

    def run_command(self, cmd, *args):
        # Wait for the process to complete and then read the output
        argstring = " ".join(args)
        command = "{0} {1} {2}".format(self.base_command, cmd, argstring)
        logline = ''.join([
            '\n'
            '----------------\n',
            'COMMAND EXECUTED\n',
            '----------------\n'
            'Command: {0}\n'.format(command)
        ])
        self.root_log.log(DEBUG, logline)
        response = self.run_command_async(cmd, *args)
        std_out, std_err = response.process.communicate()
        response.standard_out = str(std_out)
        response.standard_error = str(std_err)
        response.return_code = response.process.returncode

        logline = ''.join([
            '\n',
            '--------------\n',
            'COMMAND OUTPUT\n',
            '--------------\n',
            "Return code: {0}\n".format(str(response.return_code)),
            "stdout: {0}\n".format(std_out),
            "stderr: {0}\n".format(std_err)
        ])
        self.root_log.log(DEBUG, logline)
        # Clean up the process to avoid any leakage/wonkiness with
        # stdout/stderr
        try:
            response.process.kill()
        except OSError:
            self.root_log.log(ERROR, 'Failed to kill process {pid}.'.format(
                pid=str(response.process.pid)))

        response.process = None
        return response
