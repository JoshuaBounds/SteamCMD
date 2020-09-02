"""
App class for controlling Killing Floor 2 dedicated server.
"""


from typing import *
import re
import os
from Base.app import *


__all__ = 'KF2',


class KF2(App):
    """
    App class for controlling Killing Floor 2 dedicated server.

    :attr CUSTOM_DIRS:
        Custom directories to scan through when looking for custom
        KF-*.kfm files.
    """

    _engine_ini_subpath:   AnyStr = r"KFGame\Config\PCServer-KFEngine.ini"
    _game_ini_subpath:     AnyStr = r"KFGame\Config\PCServer-KFGame.ini"
    _cache_subpath:        AnyStr = r"KFGame\Cache"
    _workshop_section_key: AnyStr = (
        '[OnlineSubsystemSteamworks.KFWorkshopSteamworks]'
    )

    EXE_SUBPATH: AnyStr = r"Binaries\Win64\KFServer.exe"
    ARGS:        Tuple  = ('kf-burningparis',)
    ID:          int    = 232130

    CUSTOM_DIRS: Tuple  = NotImplemented

    @classmethod
    def get_game_ini_path(cls) -> AnyStr:
        """
        :return:
            Absolute path to the KFGame.ini file.
        """
        return os.path.join(cls.INSTALL_DIR, cls._game_ini_subpath)

    @classmethod
    def get_engine_ini_path(cls) -> AnyStr:
        """
        :return:
            Absolute path to the KFEngine.ini file.
        """
        return os.path.join(cls.INSTALL_DIR, cls._engine_ini_subpath)

    @classmethod
    def get_cache_path(cls) -> AnyStr:
        """
        :return:
            Absolute path to the Cache directory for workshop content.
            This directory may not exist depending on whether workshop
            content has been installed.
        """
        return os.path.join(cls.INSTALL_DIR, cls._cache_subpath)

    @classmethod
    def get_custom_dir_paths(cls) -> List[AnyStr]:
        """
        :return:
            Absolute paths to directories containing custom map data.
            Directories will be tree'd for any KF-*.kfm files.
        """
        return [
            os.path.join(cls.INSTALL_DIR, path)
            for path in cls.CUSTOM_DIRS
        ]

    @classmethod
    def rebuild_map_summaries(cls) -> NoReturn:
        """
        Rebuilds all custom map summaries for the KFGame.ini file.
        The cache, and custom dirs are scanned for any KF-*.kfm files,
        at which point any valid file names are added to the .ini file
        as custom map summaries.
        Any previous custom map summaries are discarded.
        """

        # Reads the .ini file content.
        with open(cls.get_game_ini_path()) as f:
            content = f.read()

        # Created a table of .ini sections where the .ini headers act
        # as dictionary keys.
        section_table = {}
        for section in re.split(r'\n\n+', content):
            header_line, *lines = section.split('\n')
            section_table[header_line] = lines

        # Removes any custom map summaries
        # Custom map summaries differ from vanilla ones where:
        #   Vanilla map summaries use 8 lines.
        #   Custom map summaries use 1.
        re_map_summary = re.compile(r'\[.+ KFMapSummary\]')
        for header_line, lines in tuple(section_table.items()):

            if not re_map_summary.match(header_line):
                continue
            if len(lines) != 1:
                continue

            del section_table[header_line]

        # Walks the cache dir, and all custom dirs for KF-*.kfm files.
        # All valid files found have a map summary created for them and
        # inserted into the table.
        for path in [cls.get_cache_path()] + cls.get_custom_dir_paths():
            for dir_path, _, file_names in os.walk(path):
                for file_name in file_names:

                    file_path = os.path.join(dir_path, file_name)
                    name, extension = os.path.splitext(file_name)

                    if not os.path.isfile(file_path):
                        continue
                    if not file_name.casefold().startswith('kf-'):
                        continue
                    if extension.casefold() != '.kfm':
                        continue

                    header_line = '[%s KFMapSummary]'
                    line        = 'MapName=%s'
                    section_table[header_line % name] = [line % name]

        # Converts the table back to .ini file content.
        content = '\n'.join(
            line
            for k, v in section_table.items()
            for line in [k] + v + ['']
        )

        # Writes .ini content back to file.
        with open(cls.get_game_ini_path(), 'w') as f:
            f.write(content)

    @classmethod
    def add_workshop_items(cls, items: List[int]) -> NoReturn:
        """
        Adds all given workshop content ID's to servers subscription.
        :param items:
            List of workshop ID's, given as integers.
        """

        # Reads the .ini file content.
        with open(cls.get_engine_ini_path()) as f:
            content = f.read()

        # Created a table of .ini sections where the .ini headers act
        # as dictionary keys.
        section_table = {}
        for section in re.split(r'\n\n+', content):
            header_line, *lines = section.split('\n')
            section_table[header_line] = lines

        # Get's all currently subscribed workshop items.
        existing_items = [
            int(line.split('=')[1])
            for line in section_table.setdefault(cls._workshop_section_key, [])
        ]

        # Updates the current item list
        # A set is used so that items cannot be added more than once.
        section_table[cls._workshop_section_key][:] = [
            'ServerSubscribedWorkshopItems=%s' % item
            for item in set(items + existing_items)
        ]

        # Converts the table back to .ini file content.
        content = '\n'.join(
            line
            for k, v in section_table.items()
            for line in [k] + v + ['']
        )

        # Writes .ini content back to file.
        with open(cls.get_engine_ini_path(), 'w') as f:
            f.write(content)

    @classmethod
    def remove_workshop_items(cls, items: Iterable[int] = None) -> NoReturn:
        """
        Removes workshop content from the server subscription.
        :param items:
            List of workshop ID's, given as integers.
            If None, will clear all workshop items from subscription.
        """

        # Reads the .ini file content.
        with open(cls.get_engine_ini_path()) as f:
            content = f.read()

        # Created a table of .ini sections where the .ini headers act
        # as dictionary keys.
        section_table = {}
        for section in re.split(r'\n\n+', content):
            header_line, *lines = section.split('\n')
            section_table[header_line] = lines

        # Get's all currently subscribed workshop items.
        existing_items = [
            int(line.split('=')[1])
            for line in section_table.setdefault(cls._workshop_section_key, [])
        ]

        # Updates the item list to only contain IDs that did not
        # appear in items.
        # If items is None, clears the table datum for the workshop
        # subscription.
        if items is None:
            del section_table[cls._workshop_section_key]
        else:
            section_table[cls._workshop_section_key][:] = [
                'ServerSubscribedWorkshopItems=%s' % item
                for item in existing_items
                if item not in items
            ]

        # Converts the table back to .ini file content.
        content = '\n'.join(
            line
            for k, v in section_table.items()
            for line in [k] + v + ['']
        )

        # Writes .ini content back to file.
        with open(cls.get_engine_ini_path(), 'w') as f:
            f.write(content)
