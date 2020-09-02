"""
Base class for all apps.
"""


from typing import *
from subprocess import Popen
import os


__all__ = 'App',


class App:
    """
    Base class for all apps.

    :attr INSTALL_DIR:
        Applications install directory.
    :attr EXE_SUBPATH:
        Path to the app's executable (relative to INSTALL_DIR).
    :attr ID:
        App's steam app ID.
    :attr ARGS:
        App's default launch arguments.
    """

    INSTALL_DIR: AnyStr = NotImplemented
    EXE_SUBPATH: AnyStr = NotImplemented
    ID:          int    = NotImplemented
    ARGS:        Tuple  = NotImplemented

    @classmethod
    def launch(cls) -> Popen:
        """
        Creates and returns a process for the app.
        :return:
            Apps Popen object.
        """
        return Popen(cls.get_launch_command())

    @classmethod
    def get_exe_path(cls) -> AnyStr:
        """
        :return:
            Absolute path to the app's executable.
        """
        return os.path.join(cls.INSTALL_DIR, cls.EXE_SUBPATH)

    @classmethod
    def get_launch_command(cls) -> Tuple:
        """
        :return:
            Shell command that will launch the app using current args.
        """
        return (cls.get_exe_path(),) + cls.ARGS
