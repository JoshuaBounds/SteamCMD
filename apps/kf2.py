"""
App class for controlling Killing Floor 2 dedicated server.

TODO:
    Method for automatically setting up webadmin.
    Method for automatically setting up workshop.
"""


from typing import *
import re
import os
import shutil
from apps.app import *


__all__ = 'KF2',


class KF2(App):
    """
    App class for controlling Killing Floor 2 dedicated server.

    :attr CUSTOM_DIRS:
        Custom directories to scan through when looking for custom
        KF-*.kfm files.
    """

    # Private constants.
    _engine_ini_subpath:   AnyStr = r"KFGame\Config\PCServer-KFEngine.ini"
    _game_ini_subpath:     AnyStr = r"KFGame\Config\PCServer-KFGame.ini"
    _cache_subpath:        AnyStr = r"KFGame\Cache"
    _gameinfo_section_key: AnyStr = r'[KFGame.KFGameInfo]'
    _workshop_section_key: AnyStr = (
        '[OnlineSubsystemSteamworks.KFWorkshopSteamworks]'
    )

    # Redefined attributes.
    EXE_SUBPATH: AnyStr = r"Binaries\Win64\KFServer.exe"
    ARGS:         Tuple = 'kf-burningparis',
    ID:             int = 232130

    # User defined attributes.
    CUSTOM_DIRS: Tuple = NotImplemented

    @classmethod
    def get_game_ini_path(cls) -> AnyStr:
        """
        Gets the absolute path to the KFGame.ini file.

        :return:
            Absolute path to the KFGame.ini file.
        """
        return os.path.join(cls.INSTALL_DIR, cls._game_ini_subpath)

    @classmethod
    def get_engine_ini_path(cls) -> AnyStr:
        """
        Gets the absolute path to the KFEngine.ini file.

        :return:
            Absolute path to the KFEngine.ini file.
        """
        return os.path.join(cls.INSTALL_DIR, cls._engine_ini_subpath)

    @classmethod
    def get_cache_dir(cls) -> AnyStr:
        """
        Gets the absolute path to the workshop content cache.

        :return:
            Absolute path to the Cache directory for workshop content.
            This directory may not exist depending on whether workshop
            content has been installed.
        """
        return os.path.join(cls.INSTALL_DIR, cls._cache_subpath)

    @classmethod
    def get_custom_dir_paths(cls) -> List[AnyStr]:
        """
        Gets absolute paths to directories containing custom map data.

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
        section_table = cls.read_ini_file_to_table(cls.get_game_ini_path())

        # Removes any custom map summaries from table.
        # Custom map summaries differ from vanilla ones where:
        #   Vanilla map summaries use 8 lines.
        #   Custom map summaries use 1.
        re_map_summary = re.compile(r'\[.+ KFMapSummary]')
        for header_line, lines in tuple(section_table.items()):

            if not re_map_summary.match(header_line):
                continue
            if len(lines) != 1:
                continue

            del section_table[header_line]

        # Creates a map summaries for all custom maps found in
        # registered directories.
        for name in cls.get_custom_map_names():
            summary_line, map_line = '[%s KFMapSummary]', 'MapName=%s'
            section_table[summary_line % name] = [map_line % name]

        # Writes the modified table back to file.
        cls.write_table_to_ini_file(cls.get_game_ini_path(), section_table)

    @classmethod
    def set_workshop_items(
            cls,
            items:  List[int],
            append: bool = False
    ) -> NoReturn:
        """
        Sets the workshop content ID's for the server to subscribe to.

        :param items:
            List of workshop ID's, given as integers.
        :param append:
            Appends given workshop items to any existing ones instead
            of overwriting them.
        """

        # Reads the .ini file content.
        section_table = cls.read_ini_file_to_table(cls.get_engine_ini_path())

        # Get's all currently subscribed workshop items.
        existing_items = [
            int(line.split('=')[1])
            for line in section_table.setdefault(cls._workshop_section_key, [])
            if '=' in line
        ]

        # Gets a set of both the given items, and any existing items.
        # If append is False, the existing items are not included.
        all_items = set(items + existing_items) if append else set(items)

        # Updates the current item list
        # A set is used so that items cannot be added more than once.
        section_table[cls._workshop_section_key][:] = [
            'ServerSubscribedWorkshopItems=%s' % item
            for item in all_items
        ]

        # Writes the modified table back to file.
        cls.write_table_to_ini_file(cls.get_engine_ini_path(), section_table)

    @classmethod
    def remove_workshop_items(cls, items: Iterable[int] = None) -> NoReturn:
        """
        Removes workshop content from the server subscription.

        :param items:
            List of workshop ID's, given as integers.
            If None, will clear all workshop items from subscription.
        """

        # Reads the .ini file content.
        section_table = cls.read_ini_file_to_table(cls.get_engine_ini_path())

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

        # Writes the modified table back to file.
        cls.write_table_to_ini_file(cls.get_engine_ini_path(), section_table)

    @classmethod
    def get_custom_map_names(cls) -> List:
        """
        Gets names of valid custom maps in the registered directories.

        For a map to be considered valid it must:
            Be prefixed with "kf-"
            Have the extension ".kfm"
        (name requirements are not case sensitive).
        :return:
            List of custom maps names.
        """

        # Walks the cache dir, and all custom dirs for KF-*.kfm files.
        # All valid files found are appended to names.
        names = []
        for path in [cls.get_cache_dir()] + cls.get_custom_dir_paths():
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

                    names.append(name)

        return names

    @classmethod
    def read_ini_file_to_table(cls, file_path: AnyStr) -> Dict:
        """
        Reads given .ini file to a table of header sections.

        Each section header acts as the key, and the section data is a
        list of file lines for that section.
        :param file_path:
            Path to the .ini file to read.
        :return:
            Table of .ini file data.
        """

        # Reads the .ini file content.
        with open(file_path) as f:
            content = f.read()

        # Created a table of .ini sections where the .ini headers act
        # as dictionary keys.
        section_table = {}
        for section in re.split(r'\n\n+', content):
            header_line, *lines = section.split('\n')
            section_table[header_line] = lines

        return section_table

    @classmethod
    def write_table_to_ini_file(
            cls,
            file_path: AnyStr,
            table:     Dict
    ) -> NoReturn:
        """
        Writes a given .ini file table to the given .ini file path.

        :param file_path:
            Path to the .ini file to write data to.
        :param table:
            Dict of .ini file data.
        """

        # Converts the table back to .ini file content.
        content = '\n'.join(
            line
            for k, v in table.items()
            for line in [k] + v + ['']
        )

        # Writes .ini content back to file.
        with open(file_path, 'w') as f:
            f.write(content)

    @classmethod
    def rebuild_custom_mapcycle(cls, index: int = 1) -> NoReturn:
        """
        Rebuilds custom mapcycle using custom maps from registered dirs.

        Mapcycle can eiter overwrite an existing mapcycle, or be
        appended as a new mapcycle based on the index given.
        :param index:
            Mapcycle index to write custom map cycle to. If the given
            index does not exist in file, a new custom mapcycle will be
            created following the latest mapcycle on file.
        """

        # Reads the .ini file content.
        section_table = cls.read_ini_file_to_table(cls.get_game_ini_path())

        # Gets the gameinfo section.
        gameinfo_section = section_table[cls._gameinfo_section_key]

        # Gets all lines from the gameinfo section that
        # define mapcycles.
        map_cycle_indices = []
        for i, line in enumerate(gameinfo_section):
            if line.startswith('GameMapCycles'):
                map_cycle_indices.append(i)

        # Constructs the new map cycle using names of custom maps found
        # within the registered directories.
        new_mapcycle = (
            'GameMapCycles=(Maps=('
            + ','.join('"%s"' % x for x in sorted(cls.get_custom_map_names()))
            + '))'
        )

        # If a mapcycle already exists at the given index, it will be
        # overwritten using the custom map cycle. Otherwise, regardless
        # of the index given, a new map cycle will be created and
        # inserted on the next line after the latest existing mapcycle.
        if index > len(map_cycle_indices) - 1:
            gameinfo_section.insert(map_cycle_indices[-1] + 1, new_mapcycle)
        else:
            gameinfo_section[map_cycle_indices[index]] = new_mapcycle

        # Writes the modified table back to file.
        cls.write_table_to_ini_file(cls.get_game_ini_path(), section_table)

    @classmethod
    def clear_unregistered_workshop_maps(cls) -> NoReturn:
        """
        Clears all unsubscribed workshop maps from the cache directory.

        Uses the current workshop subscription list within KFEngine.ini.
        """

        # Reads the engine.ini file to a section table.
        section_table = cls.read_ini_file_to_table(cls.get_engine_ini_path())

        # Gets the IDs for all subscribed workshop maps as strings.
        re_number = re.compile(r"\d+")
        matches = (
            re_number.search(line)
            for line in section_table[cls._workshop_section_key]
        )
        map_ids = {
            match.group(0)
            for match in matches
            if match
        }

        # Deletes any existing map caches that don't exist in the list
        # of subscribed workshop maps.
        for cache_dir in os.listdir(cls.get_cache_dir()):
            if cache_dir in map_ids:
                continue
            shutil.rmtree(os.path.join(cls.get_cache_dir(), cache_dir))
