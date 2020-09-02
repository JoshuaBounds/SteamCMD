"""
App class for controlling SteamCMD.
"""


from typing import *
from subprocess import Popen
from Base.app import *


__all__ = 'Steam',


class Steam(App):
    """
    App class for controlling SteamCMD.
    """

    EXE_SUBPATH: AnyStr = r"steamcmd.exe"
    ARGS:        Tuple  = ('+login anonymous',)

    @classmethod
    def launch_game(cls, app: Type[App]) -> NoReturn:
        """
        Launches the given app class along side steamcmd.
        steamcmd will be terminated when the app's process closes.
        :param app:
            App class that will be launched along side steamcmd.
        """

        steam_process = cls.launch()

        kf2_process = app.launch()
        kf2_process.wait()

        steam_process.terminate()
        steam_process.wait()

    @classmethod
    def update_game(cls, app: Type[App]) -> NoReturn:
        """
        Updates the app at the given steam app ID.
        :param app:
            Steam app ID for the target application to update.
        """

        args = (
            cls.get_launch_command()
            + ('+app_update %s validate' % app.ID,)
        )
        steam_process = Popen(args)
        steam_process.wait()
