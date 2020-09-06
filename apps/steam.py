"""
App class for controlling SteamCMD.
"""


from typing import *
from subprocess import Popen, CREATE_NEW_CONSOLE
from apps.app import *


__all__ = 'Steam',


class Steam(App):
    """
    App class for controlling SteamCMD.
    """

    EXE_SUBPATH: AnyStr = r"steamcmd.exe"
    ARGS:         Tuple = '+login anonymous',

    @classmethod
    def launch(cls, **kwargs: Any) -> Popen:
        """
        Creates and returns a Popen process for the app.

        :return:
            apps Popen object.
        """

        return Popen(
            cls.get_launch_args(),
            creationflags=CREATE_NEW_CONSOLE
        )

    @classmethod
    def update_game(cls, app: Union[Type[App], App]) -> NoReturn:
        """
        Updates the app at the given steam app ID.

        Creates a new constole to update the game as steams stdout
        doesn't play well with the subprocess module.
        :param app:
            Steam app ID for the target application to update.
        """

        args = (
            cls.get_launch_args()
            + ('+app_update %s validate' % app.ID, '+exit')
        )

        steam_process = Popen(args, creationflags=CREATE_NEW_CONSOLE)
        steam_process.wait()
