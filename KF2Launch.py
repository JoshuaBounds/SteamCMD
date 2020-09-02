
from Base.steam import *
from Base.kf2 import *

KF2.INSTALL_DIR = r"D:\steamCMD\steamapps\common\kf2server"
KF2.CUSTOM_DIRS = r"KFGame\BrewedPC\Maps\Custom",
KF2.rebuild_map_summaries()

Steam.INSTALL_DIR = r"D:\steamCMD"
Steam.launch_game(KF2)
