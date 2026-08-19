import os
import requests
from urllib.parse import quote

from PyQt5.QtWidgets import QLabel, QMessageBox
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap

from tools import creat_directory
from canvas_events_qt import get_pixmap
import music_player_qt
from window_qt import win_set_top

from 日志.advanced_logger import AdvancedLogger
logger = AdvancedLogger.get_logger(__name__)

server_url = "http://47.96.235.36:65431"


def download_music_files_from_server(file_path_album, music_win_name):
    file_path_all = "./音乐/下载/" + file_path_album
    creat_directory(file_path_all)

    encoded_name = quote(file_path_album)
    try:
        response = requests.get(f"{server_url}/music_download/{encoded_name}", timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"文件 '{file_path_album}' 下载失败：{str(e)}")
        QMessageBox.critical(None, "错误", f"文件 '{file_path_album}' 下载失败\n请检查网络连接后重试\n{str(e)}")
        win_set_top("音乐", music_win_name)
        return False

    if response.content.startswith(b'{"error"'):
        err_info = response.content.decode('utf-8')
        logger.error(f"文件 '{file_path_album}' 下载失败\n请重试 {err_info}")
        QMessageBox.critical(None, "错误", f"文件 '{file_path_album}' 下载失败\n请重试 {err_info}")
        win_set_top("音乐", music_win_name)
        return False

    with open(file_path_all, 'wb') as f:
        f.write(response.content)

    QMessageBox.information(None, "信息", f"文件 '{file_path_album}' 下载成功")
    win_set_top("音乐", music_win_name)
    return True


album_cover_paths = {
    "HEAVEN_BURNS_RED_Original_Sound_Track_Vol1": "./音乐/下载/HEAVEN_BURNS_RED_Original_Sound_Track_Vol1/HEAVEN_BURNS_RED_Original_Sound_Track_Vol1.jpg",
    "HEAVEN_BURNS_RED_Original_Sound_Track_Vol2": "./音乐/下载/HEAVEN_BURNS_RED_Original_Sound_Track_Vol2/HEAVEN_BURNS_RED_Original_Sound_Track_Vol2.jpg",
    "Love_Song_from_the_Water": "./音乐/下载/Love_Song_from_the_Water/Love_Song_from_the_Water.jpg",
    "麻枝准_やなぎなぎ": "./音乐/下载/麻枝准_やなぎなぎ/",
    "麻枝准_rionos": "./音乐/下载/麻枝准_rionos/",
    "佐々木恵梨": "./音乐/下载/佐々木恵梨/",
    "愛美": "./音乐/下载/愛美/",
    "She_is_Legend": "./音乐/下载/She_is_Legend/",
    "Stargazer": "./音乐/下载/Stargazer/",
    "Summer_Pockets_Original_Sound_Track": "./音乐/下载/Summer_Pockets_Original_Sound_Track/Summer_Pockets_Original_Sound_Track.jpg",
    "Summer_Pockets_REFLECTION_BLUE_Original_SoundTrack": "./音乐/下载/Summer_Pockets_REFLECTION_BLUE_Original_SoundTrack/Summer_Pockets_REFLECTION_BLUE_Original_SoundTrack.jpg",
    "CLANNAD_Original_Sound_Track": "./音乐/下载/CLANNAD_Original_Sound_Track/CLANNAD_Original_Sound_Track.png",
    "Rewrite_Original_Sound_Track": "./音乐/下载/Rewrite_Original_Sound_Track/Rewrite_Original_Sound_Track.jpg",
    "Inst_Test_Examples": "./音乐/下载/Inst_Test_Examples/"
}


def get_album_cover_path(all_albun_name, file_name):
    if all_albun_name == "麻枝准_やなぎなぎ":
        file_name = file_name.replace("29.Sailing Ship", "Welcome to the Dying Season")
        return album_cover_paths["麻枝准_やなぎなぎ"] + file_name.replace("flac", "jpg")
    elif all_albun_name == "麻枝准_rionos":
        return album_cover_paths["麻枝准_rionos"] + file_name.replace("flac", "jpg")
    elif all_albun_name == "佐々木恵梨":
        return album_cover_paths["佐々木恵梨"] + file_name.replace("flac", "jpg")
    elif all_albun_name == "She_is_Legend":
        file_name = file_name.replace("03.陽のさす向こうへ", "02.春眠旅団")
        file_name = file_name.replace("11.World We Changed", "02.春眠旅団")
        file_name = file_name.replace("09.複葉機とオールトの雲", "Perfect Smile")
        file_name = file_name.replace("10.Arch of Light Alternative", "Perfect Smile")
        return album_cover_paths["She_is_Legend"] + file_name.replace("flac", "jpg")
    elif all_albun_name == "Inst_Test_Examples":
        return album_cover_paths["Inst_Test_Examples"] + file_name.replace("flac", "jpg")
    elif all_albun_name == "Stargazer":
        return album_cover_paths["Stargazer"] + file_name.replace("flac", "jpg")
    else:
        return album_cover_paths[all_albun_name]


def _set_cover(album_cover_path, all_albun_name):
    frame = music_player_qt.play_info_frame
    if frame is None:
        return
    layout = frame.layout()
    if layout is None:
        return

    # 移除旧的封面
    while layout.count() > 1:
        item = layout.takeAt(0)
        w = item.widget()
        if w:
            w.deleteLater()

    if "Original_Sound_Track" in all_albun_name:
        pixmap = get_pixmap(album_cover_path, (336, 300))
    else:
        pixmap = get_pixmap(album_cover_path, (300, 300))

    cover_label = QLabel()
    cover_label.setPixmap(pixmap)
    cover_label.setAlignment(Qt.AlignCenter)
    cover_label.setFixedSize(500, 300)
    layout.insertWidget(0, cover_label)


def safe_stop():
    if music_player_qt.PlayerApp:
        QTimer.singleShot(0, music_player_qt.PlayerApp.stop)


def music_handle(all_albun_name, disc_name, file_name, music_win_name):
    album_cover_path = get_album_cover_path(all_albun_name, file_name)
    _set_cover(album_cover_path, all_albun_name)

    file_path_album = all_albun_name + "/" + disc_name + "/" + file_name
    file_path_all = "./音乐/下载/" + file_path_album
    if not os.path.exists(file_path_all):
        if not download_music_files_from_server(file_path_album, music_win_name):
            safe_stop()
            return

    safe_stop()
    def _load_and_play():
        if music_player_qt.PlayerApp is None:
            logger.error("PlayerApp 为 None，无法加载音乐")
            QMessageBox.critical(None, "错误", "播放器未初始化，请重新打开音乐窗口")
            return
        try:
            music_player_qt.PlayerApp.load_file(file_path_all)
            # music_player_qt.PlayerApp.play()
        except Exception as e:
            logger.error(f"加载或播放失败：{e}")
            raise
    QTimer.singleShot(0, _load_and_play)
