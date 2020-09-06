"""
Alias functions for launching TPTIAP community servers.
"""


from typing import *
from subprocess import Popen
import time
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from Apps.steam import *
from Apps.kf2 import *


__all__ = 'start_kf2_server', 'start_kf2_server_loop'


def start_kf2_server(
        steam_dir:           AnyStr,
        kf2_dir:             AnyStr,
        kf2_custom_dirs:     Tuple,
        google_creds_file:   AnyStr,
        google_sheet_name:   AnyStr,
        google_sheet_column: int
) -> Tuple[Popen, Popen]:
    """
    Starts of the KF2 server using the TPTIAP community preset.

    Startup process:
        - Gets all workshop ID's from the "KF2 New Maps" google sheet
            and regenerates server's workshop subscription list.
        - Starts the server and waits 5 minutes to give the server time
            to download any new workshop maps before stopping again.
        - Rebuilds the servers custom map summaries and mapcycle.
        - Launches the server and returns the steam, and kf2 process's
    :param steam_dir:
        Path to steamcmd's install directory.
    :param kf2_dir:
        Path to Killing Floor 2 server install directory.
    :param kf2_custom_dirs:
        Tuple of paths to custom directories to scan for custom maps.
        Paths are relative to the servers install directory.
    :param google_creds_file:
        Credentials file for the google api that has access to the
        KF2 maps google sheet.
    :param google_sheet_name:
        Name of the google sheet to read for workshop map ID's.
    :param google_sheet_column:
        Column of the google sheet to read for workshop map ID's.
        Will only read cells that contain only numbers, anything else
        is ignored.
    :return:
        Tuple containing the steam and kf2 Popen objects.
    """

    # Sets the install directories for Steam and KF2.
    # Sets KF2's custom map directories.
    Steam.INSTALL_DIR = steam_dir
    KF2.INSTALL_DIR = kf2_dir
    KF2.CUSTOM_DIRS = kf2_custom_dirs

    # Gets all the accepted workshop ID's from the "KF2 New Maps"
    # google sheet and adds them to the servers subscribed
    # workshop content.
    scope = (
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive"
    )
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        google_creds_file,
        scope
    )
    client = gspread.authorize(credentials)
    sheet = client.open(google_sheet_name).sheet1
    re_number = re.compile(r"\d+")
    KF2.set_workshop_items([
        int(cell)
        for cell in sheet.col_values(google_sheet_column)
        if re_number.match(cell)
    ])

    # Launches Steam and KF2 then waits 5 minutes to give the server
    # time to download any new workshop content; then terminates
    # the process's.
    steam = Steam.launch()
    kf2 = KF2.launch()
    time.sleep(60.0 * 5)
    steam.terminate()
    kf2.terminate()
    steam.wait()
    kf2.wait()

    # Rebuilds the custom map summaries and custom map cycles.
    KF2.rebuild_map_summaries()
    KF2.rebuild_custom_mapcycle()

    # Launches the KF2 server.
    return Steam.launch(), KF2.launch()


def start_kf2_server_loop(
        restart_hour: int,
        *args:        Any,
        **kwargs:     Any
) -> NoReturn:
    """
    Restarts and updates the TPTIAP KF2 server every morning.

    Server will restart every morning at the given hour in local time.
    :param restart_hour:
        Hour of the day (local time) at which the server will restart
        in order to update any workshop map data.
    :param args:
        Given to `start_kf2_server()`.
    :param kwargs:
        Given to `start_kf2_server()`.
    """

    # Main loop that restarts the server at 00:00 local time each day.
    while True:

        # Starts the server and returns the steam and kf2 process.
        steam, kf2 = start_kf2_server(*args, **kwargs)

        # Loops until a full day has passed.
        is_restart_hour = False
        while True:
            hour = time.localtime().tm_hour
            if hour == restart_hour and is_restart_hour:
                break
            if hour != restart_hour:
                is_restart_hour = True
            time.sleep(60)

        # Terminates the server processes.
        steam.terminate()
        kf2.terminate()
        steam.wait()
        kf2.wait()
