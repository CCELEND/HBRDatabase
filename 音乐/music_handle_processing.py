
import os
import requests
from tkinter import messagebox
from urllib.parse import quote

from tools import creat_directory
from canvas_events import get_photo, create_canvas_with_image
import music_player

from 日志.advanced_logger import AdvancedLogger
logger = AdvancedLogger.get_logger(__name__)

server_url = "http://47.96.235.36:65431"

def download_music_files_from_server(file_path_album):
    file_path_all = "./音乐/下载/" + file_path_album
    creat_directory(file_path_all)

    # 编码特殊字符
    encoded_name = quote(file_path_album)
    # 服务器响应
    response = requests.get(f"{server_url}/music_download/{encoded_name}")

    if response.content.startswith(b'{"error"'):
        err_info = response.content.decode('utf-8')
        logger.error(f"文件 '{file_path_album}' 下载失败\n请重试 {err_info}")
        messagebox.showerror("错误", f"文件 '{file_path_album}' 下载失败\n请重试 {err_info}")
        return False

    # 保存文件
    with open(file_path_all, 'wb') as f:
        f.write(response.content)

    return True


album_cover_paths={
    "HEAVEN_BURNS_RED_Original_Sound_Track_Vol1":"./音乐/下载/HEAVEN_BURNS_RED_Original_Sound_Track_Vol1/HEAVEN_BURNS_RED_Original_Sound_Track_Vol1.jpg",
    "HEAVEN_BURNS_RED_Original_Sound_Track_Vol2":"./音乐/下载/HEAVEN_BURNS_RED_Original_Sound_Track_Vol2/HEAVEN_BURNS_RED_Original_Sound_Track_Vol2.jpg",
    "Love_Song_from_the_Water":"./音乐/下载/Love_Song_from_the_Water/Love_Song_from_the_Water.jpg",
    "麻枝准_やなぎなぎ":"./音乐/下载/麻枝准_やなぎなぎ/",
    "麻枝准_rionos":"./音乐/下载/麻枝准_rionos/",
    "佐々木恵梨":"./音乐/下载/佐々木恵梨/",
    "She_is_Legend":"./音乐/下载/She_is_Legend/",
    "Stargazer":"./音乐/下载/Stargazer/",
    "Summer_Pockets_Original_Sound_Track":"./音乐/下载/Summer_Pockets_Original_Sound_Track/Summer_Pockets_Original_Sound_Track.jpg",
    "CLANNAD_Original_Sound_Track":"./音乐/下载/CLANNAD_Original_Sound_Track/CLANNAD_Original_Sound_Track.png",
    "Inst_Test_Examples":"./音乐/下载/Inst_Test_Examples/"

}
def get_album_cover_path(all_albun_name, file_name):
    if all_albun_name == "麻枝准_やなぎなぎ":
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


# Tkinter 是单线程的 GUI，所有 UI 更新（如按钮状态变化）必须在主线程中完成
# 确保操作在主线程中执行
def safe_stop():
    if music_player.PlayerApp:
        music_player.PlayerApp.frame.after(0, music_player.PlayerApp.stop)
        # 等待 Tkinter 处理事件队列
        music_player.PlayerApp.frame.update_idletasks()

def music_handle(all_albun_name, disc_name, file_name):

    # 更新窗口UI 例如专辑图片
    album_cover_path = get_album_cover_path(all_albun_name, file_name)
    if "Original_Sound_Track" in all_albun_name:
        photo=get_photo(album_cover_path, (336,300))
        create_canvas_with_image(music_player.play_info_frame, photo, 500, 300, 61, 0, 0, 0, padx=10, pady=0)
    else:
        photo=get_photo(album_cover_path, (300,300))
        create_canvas_with_image(music_player.play_info_frame, photo, 500, 300, 79, 0, 0, 0, padx=10, pady=0)


    file_path_album = all_albun_name + "/" + disc_name + "/" + file_name
    file_path_all = "./音乐/下载/" + file_path_album
    if not os.path.exists(file_path_all):
        if not download_music_files_from_server(file_path_album):
            safe_stop()
            return

    safe_stop()
    music_player.PlayerApp.frame.after(0, lambda: music_player.PlayerApp.load_file(file_path_all))
