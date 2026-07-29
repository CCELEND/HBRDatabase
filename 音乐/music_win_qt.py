import types

from PyQt5.QtWidgets import QMessageBox, QWidget, QHBoxLayout, QVBoxLayout

from window_qt import set_window_icon, creat_Toplevel
from window_qt import win_open_manage, win_close_manage, is_win_open, win_set_top
from tools import load_json

from music_list_qt import ExpandableList
from music_player_qt import FLACPlayerApp
import music_player_qt

from 日志.advanced_logger import AdvancedLogger
logger = AdvancedLogger.get_logger(__name__)


def creat_music_win():
    if is_win_open("音乐", __name__):
        win_set_top("音乐", __name__)
        return "break"

    music_win_frame = creat_Toplevel("音乐", 850, 575, x=190, y=140)
    set_window_icon(music_win_frame, "./音乐/Sound.ico")
    music_win_frame.setFixedSize(850, 575)

    central_widget = QWidget()
    music_win_frame.setCentralWidget(central_widget)
    main_layout = QHBoxLayout(central_widget)
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.setSpacing(0)

    categories = load_json("./音乐/music.json")
    ListApp = ExpandableList(central_widget, categories, 0, 0, music_win_name=__name__)
    main_layout.addWidget(ListApp.frame, 7)

    music_player_qt.play_info_frame = QWidget(central_widget)
    music_player_qt.play_info_frame.setLayout(QVBoxLayout())
    main_layout.addWidget(music_player_qt.play_info_frame, 10)

    try:
        music_player_qt.PlayerApp = FLACPlayerApp(music_player_qt.play_info_frame, 0, 0)
    except Exception as e:
        logger.error(str(e))
        QMessageBox.critical(None, "错误", f"请重试：{str(e)}")
        music_win_frame.close()
        return

    win_open_manage(music_win_frame, __name__)

    def on_close(self, event):
        try:
            music_player_qt.PlayerApp.on_close()
        except Exception:
            pass
        win_close_manage(music_win_frame, __name__)
        event.accept()

    music_win_frame.closeEvent = types.MethodType(on_close, music_win_frame)
